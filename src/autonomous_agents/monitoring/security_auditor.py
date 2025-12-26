"""SecurityAuditor - Audits security vulnerabilities in the codebase."""

import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

from ..base_autonomous_agent import BaseAutonomousAgent


class SecurityAuditor(BaseAutonomousAgent):
    """
    Audits security vulnerabilities and potential issues.
    
    Tracks:
    - Dependency vulnerabilities (pip-audit)
    - Hardcoded secrets (basic pattern matching)
    - Security score (0-100)
    
    Interval: 1 hour (3600 seconds)
    """
    
    def __init__(self):
        super().__init__(
            name="SecurityAuditor",
            layer="monitoring",
            interval_seconds=3600  # 1 hour
        )
        self.src_path = Path("src")
        
        # Patterns that might indicate secrets
        self.secret_patterns = [
            r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']',
            r'(?i)(api_key|apikey|api-key)\s*=\s*["\'][^"\']+["\']',
            r'(?i)(secret|token)\s*=\s*["\'][^"\']+["\']',
            r'(?i)(aws_access_key|aws_secret)\s*=\s*["\'][^"\']+["\']',
        ]
    
    async def analyze(self) -> Dict[str, Any]:
        """
        Run security audits.
        
        Returns:
            Dictionary with security analysis results
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'vulnerabilities': self._check_vulnerabilities(),
            'secrets': self._scan_for_secrets(),
            'permissions': self._check_permissions()
        }
        
        # Calculate security score
        vuln_count = results['vulnerabilities'].get('count', 0)
        secret_count = results['secrets'].get('count', 0)
        
        # Score calculation
        score = 100.0
        score -= vuln_count * 10  # -10 per vulnerability
        score -= secret_count * 15  # -15 per potential secret
        
        results['security_score'] = max(0, min(100, score))
        
        # Update metrics
        self.metrics['security_score'] = results['security_score']
        self.metrics['vulnerabilities'] = vuln_count
        self.metrics['potential_secrets'] = secret_count
        
        logger.info(
            f"[{self.name}] Security Score: {results['security_score']:.1f}/100 "
            f"(Vulns: {vuln_count}, Secrets: {secret_count})"
        )
        
        return results
    
    async def plan(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create plans to address security issues.
        
        Args:
            analysis: Results from analyze()
            
        Returns:
            List of improvement plans
        """
        plans = []
        
        # Plan for vulnerabilities
        vulns = analysis.get('vulnerabilities', {})
        if vulns.get('count', 0) > 0:
            plans.append({
                'type': 'vulnerability_alert',
                'priority': 10,  # Highest priority
                'description': f"Found {vulns['count']} dependency vulnerabilities",
                'vulnerabilities': vulns.get('details', [])
            })
        
        # Plan for potential secrets
        secrets = analysis.get('secrets', {})
        if secrets.get('count', 0) > 0:
            plans.append({
                'type': 'secret_alert',
                'priority': 10,  # Highest priority
                'description': f"Found {secrets['count']} potential hardcoded secrets",
                'files': secrets.get('files', [])
            })
        
        # Save improvement suggestion if score is low
        if analysis.get('security_score', 100) < 80:
            self._save_improvement_suggestion({
                'category': 'security',
                'priority': 10,
                'title': 'Security Issues Detected',
                'description': f"Security score is {analysis['security_score']:.1f}/100. "
                              f"Found {vulns.get('count', 0)} vulnerabilities and "
                              f"{secrets.get('count', 0)} potential secrets.",
                'estimated_impact': 0.3,
                'analysis': {
                    'security_score': analysis['security_score'],
                    'vulnerabilities': vulns.get('count', 0),
                    'secrets': secrets.get('count', 0)
                }
            })
        
        return plans
    
    async def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a security improvement plan.
        
        Args:
            plan: An improvement plan
            
        Returns:
            Execution result
        """
        plan_type = plan.get('type', '')
        
        if plan_type == 'vulnerability_alert':
            # Log critical alert
            logger.critical(f"[{self.name}] SECURITY ALERT: {plan['description']}")
            for vuln in plan.get('vulnerabilities', [])[:5]:
                logger.warning(f"  - {vuln}")
            
            return {
                'status': 'logged',
                'message': 'Vulnerability alert logged for immediate review',
                'action': 'vulnerability_alert'
            }
        
        elif plan_type == 'secret_alert':
            # Log critical alert
            logger.critical(f"[{self.name}] SECURITY ALERT: {plan['description']}")
            for file in plan.get('files', [])[:5]:
                logger.warning(f"  - {file}")
            
            return {
                'status': 'logged',
                'message': 'Secret exposure alert logged for immediate review',
                'action': 'secret_alert'
            }
        
        else:
            return {
                'status': 'skipped',
                'message': f"Unknown plan type: {plan_type}",
                'action': plan_type
            }
    
    def _check_vulnerabilities(self) -> Dict[str, Any]:
        """Check for dependency vulnerabilities using pip-audit."""
        result = {
            'available': False,
            'count': 0,
            'details': []
        }
        
        try:
            # Check if pip-audit is available
            version_check = subprocess.run(
                ['pip-audit', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if version_check.returncode != 0:
                logger.info(f"[{self.name}] pip-audit not available")
                return result
            
            result['available'] = True
            
            # Run pip-audit
            audit_result = subprocess.run(
                ['pip-audit', '--format=json'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if audit_result.stdout:
                try:
                    import json
                    vulns = json.loads(audit_result.stdout)
                    result['count'] = len(vulns)
                    result['details'] = [
                        f"{v.get('name', 'unknown')} {v.get('version', '')}: {v.get('vulns', [{}])[0].get('id', 'unknown')}"
                        for v in vulns[:10]
                    ]
                except:
                    pass
            
        except subprocess.TimeoutExpired:
            logger.warning(f"[{self.name}] pip-audit timed out")
            result['error'] = 'timeout'
        except FileNotFoundError:
            logger.info(f"[{self.name}] pip-audit not installed")
            result['error'] = 'not_found'
        except Exception as e:
            logger.error(f"[{self.name}] pip-audit error: {e}")
            result['error'] = str(e)
        
        return result
    
    def _scan_for_secrets(self) -> Dict[str, Any]:
        """Scan source code for potential hardcoded secrets."""
        result = {
            'count': 0,
            'files': []
        }
        
        if not self.src_path.exists():
            return result
        
        try:
            for py_file in self.src_path.rglob('*.py'):
                try:
                    content = py_file.read_text()
                    
                    for pattern in self.secret_patterns:
                        matches = re.findall(pattern, content)
                        if matches:
                            result['count'] += len(matches)
                            result['files'].append(str(py_file))
                            break  # Only count file once
                            
                except Exception as e:
                    logger.debug(f"[{self.name}] Error scanning {py_file}: {e}")
            
            # Deduplicate files
            result['files'] = list(set(result['files']))
            
        except Exception as e:
            logger.warning(f"[{self.name}] Error scanning for secrets: {e}")
            result['error'] = str(e)
        
        return result
    
    def _check_permissions(self) -> Dict[str, Any]:
        """Check file permissions (basic check)."""
        result = {
            'checked': True,
            'issues': []
        }
        
        # Check if .env file exists and is readable by others
        env_file = Path('.env')
        if env_file.exists():
            try:
                mode = env_file.stat().st_mode
                # Check if others have read permission (o+r = 0o004)
                if mode & 0o004:
                    result['issues'].append('.env is world-readable')
            except:
                pass
        
        return result
