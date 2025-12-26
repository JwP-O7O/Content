"""DependencyScanner - Scans and manages project dependencies."""

import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

from ..base_autonomous_agent import BaseAutonomousAgent


class DependencyScanner(BaseAutonomousAgent):
    """
    Scans project dependencies for updates and issues.
    
    Tracks:
    - Outdated packages
    - Available updates
    - Breaking changes warnings
    
    Interval: 24 hours (86400 seconds)
    """
    
    def __init__(self):
        super().__init__(
            name="DependencyScanner",
            layer="monitoring",
            interval_seconds=86400  # 24 hours
        )
        self.requirements_files = [
            Path("requirements.txt"),
            Path("requirements-dev.txt"),
            Path("requirements-minimal.txt")
        ]
    
    async def analyze(self) -> Dict[str, Any]:
        """
        Analyze project dependencies.
        
        Returns:
            Dictionary with dependency analysis results
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'outdated': self._get_outdated_packages(),
            'installed': self._get_installed_packages(),
            'requirements': self._analyze_requirements_files()
        }
        
        # Count outdated
        outdated_count = len(results['outdated'].get('packages', []))
        results['outdated_count'] = outdated_count
        
        # Calculate freshness score
        total_packages = results['installed'].get('count', 1)
        freshness = 100 - (outdated_count / max(total_packages, 1) * 100)
        results['freshness_score'] = max(0, min(100, freshness))
        
        # Update metrics
        self.metrics['outdated_count'] = outdated_count
        self.metrics['freshness_score'] = results['freshness_score']
        self.metrics['total_packages'] = total_packages
        
        logger.info(
            f"[{self.name}] Freshness Score: {results['freshness_score']:.1f}/100 "
            f"({outdated_count} outdated packages)"
        )
        
        return results
    
    async def plan(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create plans for dependency updates.
        
        Args:
            analysis: Results from analyze()
            
        Returns:
            List of improvement plans
        """
        plans = []
        
        outdated = analysis.get('outdated', {}).get('packages', [])
        
        # Plan for minor/patch updates (safe to auto-update)
        safe_updates = [
            p for p in outdated 
            if self._is_safe_update(p.get('current', ''), p.get('latest', ''))
        ]
        
        if safe_updates:
            plans.append({
                'type': 'safe_updates',
                'priority': 4,
                'description': f"Found {len(safe_updates)} safe (minor/patch) updates",
                'packages': safe_updates[:10],  # Limit to 10
                'requires_approval': False
            })
        
        # Plan for major updates (need manual review)
        major_updates = [p for p in outdated if p not in safe_updates]
        
        if major_updates:
            plans.append({
                'type': 'major_updates',
                'priority': 3,
                'description': f"Found {len(major_updates)} major updates requiring review",
                'packages': major_updates[:10],
                'requires_approval': True
            })
        
        # Save suggestion if many packages are outdated
        if len(outdated) > 5:
            self._save_improvement_suggestion({
                'category': 'dependencies',
                'priority': 5,
                'title': 'Multiple Outdated Dependencies',
                'description': f"{len(outdated)} packages have updates available. "
                              f"Consider updating to improve security and features.",
                'estimated_impact': 0.1,
                'packages': [p.get('name') for p in outdated[:20]]
            })
        
        return plans
    
    async def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a dependency update plan.
        
        Args:
            plan: An improvement plan
            
        Returns:
            Execution result
        """
        plan_type = plan.get('type', '')
        
        if plan_type == 'safe_updates':
            # Log the recommendations (don't auto-update dependencies)
            packages = plan.get('packages', [])
            pkg_names = [p.get('name', 'unknown') for p in packages]
            
            logger.info(f"[{self.name}] Safe updates available: {', '.join(pkg_names[:5])}")
            
            return {
                'status': 'logged',
                'message': f"Logged {len(packages)} safe update recommendations",
                'action': 'safe_updates',
                'packages': pkg_names
            }
        
        elif plan_type == 'major_updates':
            # Log for manual review
            packages = plan.get('packages', [])
            pkg_names = [p.get('name', 'unknown') for p in packages]
            
            logger.info(f"[{self.name}] Major updates available (review needed): {', '.join(pkg_names[:5])}")
            
            return {
                'status': 'logged',
                'message': f"Logged {len(packages)} major updates for manual review",
                'action': 'major_updates',
                'packages': pkg_names
            }
        
        else:
            return {
                'status': 'skipped',
                'message': f"Unknown plan type: {plan_type}",
                'action': plan_type
            }
    
    def _get_outdated_packages(self) -> Dict[str, Any]:
        """Get list of outdated packages."""
        result = {
            'packages': [],
            'error': None
        }
        
        try:
            output = subprocess.run(
                ['pip', 'list', '--outdated', '--format=json'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if output.stdout:
                try:
                    packages = json.loads(output.stdout)
                    result['packages'] = [
                        {
                            'name': p.get('name', ''),
                            'current': p.get('version', ''),
                            'latest': p.get('latest_version', '')
                        }
                        for p in packages
                    ]
                except json.JSONDecodeError:
                    result['error'] = 'json_parse_error'
            
        except subprocess.TimeoutExpired:
            result['error'] = 'timeout'
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _get_installed_packages(self) -> Dict[str, Any]:
        """Get count of installed packages."""
        result = {
            'count': 0,
            'error': None
        }
        
        try:
            output = subprocess.run(
                ['pip', 'list', '--format=json'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if output.stdout:
                try:
                    packages = json.loads(output.stdout)
                    result['count'] = len(packages)
                except json.JSONDecodeError:
                    pass
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _analyze_requirements_files(self) -> Dict[str, Any]:
        """Analyze requirements files."""
        result = {
            'files': [],
            'total_requirements': 0
        }
        
        for req_file in self.requirements_files:
            if req_file.exists():
                try:
                    content = req_file.read_text()
                    lines = [l.strip() for l in content.split('\n') 
                            if l.strip() and not l.startswith('#')]
                    result['files'].append({
                        'name': str(req_file),
                        'count': len(lines)
                    })
                    result['total_requirements'] += len(lines)
                except:
                    pass
        
        return result
    
    def _is_safe_update(self, current: str, latest: str) -> bool:
        """
        Check if an update is safe (minor/patch only).
        
        Args:
            current: Current version string (e.g., "1.2.3")
            latest: Latest version string (e.g., "1.2.4")
            
        Returns:
            True if safe (same major version), False otherwise
        """
        try:
            current_parts = current.split('.')
            latest_parts = latest.split('.')
            
            if len(current_parts) >= 1 and len(latest_parts) >= 1:
                # Same major version = safe
                return current_parts[0] == latest_parts[0]
        except:
            pass
        
        return False
