"""CodeHealthMonitor - Monitors code quality and health metrics."""

import subprocess
import json
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

from ..base_autonomous_agent import BaseAutonomousAgent


class CodeHealthMonitor(BaseAutonomousAgent):
    """
    Monitors code health metrics and auto-fixes issues when safe.
    
    Tracks:
    - Linting errors/warnings (Ruff)
    - Type checking issues (MyPy)
    - Code complexity
    - Overall health score (0-100)
    
    Interval: 30 minutes (1800 seconds)
    """
    
    def __init__(self):
        super().__init__(
            name="CodeHealthMonitor",
            layer="monitoring",
            interval_seconds=1800  # 30 minutes
        )
        self.src_path = Path("src")
        self.health_history: List[float] = []
    
    async def analyze(self) -> Dict[str, Any]:
        """
        Run code quality checks (Ruff and MyPy).
        
        Returns:
            Dictionary with analysis results including health score
        """
        results = {
            'ruff': self._run_ruff(),
            'mypy': self._run_mypy(),
            'file_stats': self._get_file_stats()
        }
        
        # Calculate health score
        ruff_issues = results['ruff'].get('issue_count', 0)
        mypy_issues = results['mypy'].get('issue_count', 0)
        total_files = results['file_stats'].get('python_files', 1)
        
        # Score formula: 100 - (issues per file * penalty)
        issues_per_file = (ruff_issues + mypy_issues) / max(total_files, 1)
        health_score = max(0, min(100, 100 - (issues_per_file * 5)))
        
        results['health_score'] = round(health_score, 1)
        results['total_issues'] = ruff_issues + mypy_issues
        
        # Update metrics
        self.metrics['health_score'] = results['health_score']
        self.metrics['total_issues'] = results['total_issues']
        self.metrics['ruff_issues'] = ruff_issues
        self.metrics['mypy_issues'] = mypy_issues
        
        # Track history
        self.health_history.append(health_score)
        if len(self.health_history) > 100:
            self.health_history = self.health_history[-100:]
        
        logger.info(
            f"[{self.name}] Health Score: {health_score:.1f}/100 "
            f"(Ruff: {ruff_issues}, MyPy: {mypy_issues})"
        )
        
        return results
    
    async def plan(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create plans to fix code health issues.
        
        Args:
            analysis: Results from analyze()
            
        Returns:
            List of improvement plans
        """
        plans = []
        
        # Plan 1: Auto-fix Ruff issues if any exist
        if analysis.get('ruff', {}).get('issue_count', 0) > 0:
            plans.append({
                'type': 'ruff_autofix',
                'priority': 7,
                'description': 'Auto-fix Ruff linting issues',
                'fixable_count': analysis['ruff'].get('fixable_count', 0),
                'requires_approval': False
            })
        
        # Plan 2: Format code if there are style issues
        if analysis.get('ruff', {}).get('has_format_issues', False):
            plans.append({
                'type': 'ruff_format',
                'priority': 5,
                'description': 'Format code with Ruff',
                'requires_approval': False
            })
        
        # Plan 3: Save improvement suggestions for manual review
        if analysis.get('health_score', 100) < 80:
            self._save_improvement_suggestion({
                'category': 'code_health',
                'priority': 8,
                'title': 'Code Health Below Threshold',
                'description': f"Health score is {analysis['health_score']:.1f}/100. "
                              f"Found {analysis['total_issues']} issues.",
                'estimated_impact': 0.1,
                'analysis': {
                    'health_score': analysis['health_score'],
                    'ruff_issues': analysis['ruff'].get('issue_count', 0),
                    'mypy_issues': analysis['mypy'].get('issue_count', 0)
                }
            })
        
        return plans
    
    async def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a code health improvement plan.
        
        Args:
            plan: An improvement plan
            
        Returns:
            Execution result
        """
        plan_type = plan.get('type', '')
        
        if plan_type == 'ruff_autofix':
            return self._execute_ruff_fix()
        
        elif plan_type == 'ruff_format':
            return self._execute_ruff_format()
        
        else:
            return {
                'status': 'skipped',
                'message': f"Unknown plan type: {plan_type}",
                'action': plan_type
            }
    
    def _run_ruff(self) -> Dict[str, Any]:
        """Run Ruff linter and return results."""
        result = {
            'available': False,
            'issue_count': 0,
            'fixable_count': 0,
            'has_format_issues': False,
            'issues': []
        }
        
        try:
            # Check if ruff is available
            version_check = subprocess.run(
                ['ruff', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if version_check.returncode != 0:
                logger.warning(f"[{self.name}] Ruff not available")
                return result
            
            result['available'] = True
            result['version'] = version_check.stdout.strip()
            
            # Run ruff check
            check_result = subprocess.run(
                ['ruff', 'check', str(self.src_path), '--output-format=json'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if check_result.stdout:
                try:
                    issues = json.loads(check_result.stdout)
                    result['issue_count'] = len(issues)
                    result['fixable_count'] = sum(1 for i in issues if i.get('fix'))
                    result['issues'] = issues[:20]  # Keep first 20 for logging
                except json.JSONDecodeError:
                    # Count lines as issues
                    result['issue_count'] = len(check_result.stdout.strip().split('\n'))
            
            # Check format issues
            format_check = subprocess.run(
                ['ruff', 'format', '--check', str(self.src_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            result['has_format_issues'] = format_check.returncode != 0
            
        except subprocess.TimeoutExpired:
            logger.warning(f"[{self.name}] Ruff timed out")
            result['error'] = 'timeout'
        except FileNotFoundError:
            logger.warning(f"[{self.name}] Ruff not found")
            result['error'] = 'not_found'
        except Exception as e:
            logger.error(f"[{self.name}] Ruff error: {e}")
            result['error'] = str(e)
        
        return result
    
    def _run_mypy(self) -> Dict[str, Any]:
        """Run MyPy type checker and return results."""
        result = {
            'available': False,
            'issue_count': 0,
            'issues': []
        }
        
        try:
            # Check if mypy is available
            version_check = subprocess.run(
                ['mypy', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if version_check.returncode != 0:
                logger.warning(f"[{self.name}] MyPy not available")
                return result
            
            result['available'] = True
            result['version'] = version_check.stdout.strip()
            
            # Run mypy (ignore missing imports to avoid noise)
            check_result = subprocess.run(
                ['mypy', str(self.src_path), '--ignore-missing-imports', '--no-error-summary'],
                capture_output=True,
                text=True,
                timeout=180
            )
            
            if check_result.stdout:
                lines = [l for l in check_result.stdout.strip().split('\n') if l and 'error:' in l]
                result['issue_count'] = len(lines)
                result['issues'] = lines[:20]  # Keep first 20 for logging
            
        except subprocess.TimeoutExpired:
            logger.warning(f"[{self.name}] MyPy timed out")
            result['error'] = 'timeout'
        except FileNotFoundError:
            logger.warning(f"[{self.name}] MyPy not found")
            result['error'] = 'not_found'
        except Exception as e:
            logger.error(f"[{self.name}] MyPy error: {e}")
            result['error'] = str(e)
        
        return result
    
    def _get_file_stats(self) -> Dict[str, Any]:
        """Get statistics about Python files in the project."""
        stats = {
            'python_files': 0,
            'total_lines': 0
        }
        
        try:
            for py_file in self.src_path.rglob('*.py'):
                stats['python_files'] += 1
                try:
                    stats['total_lines'] += sum(1 for _ in open(py_file))
                except:
                    pass
        except Exception as e:
            logger.warning(f"[{self.name}] Error getting file stats: {e}")
        
        return stats
    
    def _execute_ruff_fix(self) -> Dict[str, Any]:
        """Execute Ruff auto-fix."""
        try:
            result = subprocess.run(
                ['ruff', 'check', str(self.src_path), '--fix'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            return {
                'status': 'success' if result.returncode == 0 else 'partial',
                'message': 'Applied Ruff auto-fixes',
                'action': 'ruff_autofix',
                'output': result.stdout[:500] if result.stdout else None
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'action': 'ruff_autofix'
            }
    
    def _execute_ruff_format(self) -> Dict[str, Any]:
        """Execute Ruff formatting."""
        try:
            result = subprocess.run(
                ['ruff', 'format', str(self.src_path)],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            return {
                'status': 'success' if result.returncode == 0 else 'partial',
                'message': 'Formatted code with Ruff',
                'action': 'ruff_format',
                'output': result.stdout[:500] if result.stdout else None
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'action': 'ruff_format'
            }
