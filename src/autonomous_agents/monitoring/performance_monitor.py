"""PerformanceMonitor - Monitors system performance and identifies bottlenecks."""

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

from ..base_autonomous_agent import BaseAutonomousAgent

# Try to import psutil (optional)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class PerformanceMonitor(BaseAutonomousAgent):
    """
    Monitors system performance metrics.
    
    Tracks:
    - CPU and memory usage
    - Disk usage
    - Process statistics
    - Log file sizes
    - Performance score (0-100)
    
    Interval: 15 minutes (900 seconds)
    """
    
    def __init__(self):
        super().__init__(
            name="PerformanceMonitor",
            layer="monitoring",
            interval_seconds=900  # 15 minutes
        )
        self.thresholds = {
            'cpu_warning': 80,
            'memory_warning': 80,
            'disk_warning': 90
        }
        self.performance_history: List[Dict[str, Any]] = []
    
    async def analyze(self) -> Dict[str, Any]:
        """
        Analyze system performance metrics.
        
        Returns:
            Dictionary with performance metrics and score
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'psutil_available': PSUTIL_AVAILABLE
        }
        
        if PSUTIL_AVAILABLE:
            # System metrics
            results['cpu'] = self._get_cpu_metrics()
            results['memory'] = self._get_memory_metrics()
            results['disk'] = self._get_disk_metrics()
            results['processes'] = self._get_process_metrics()
        else:
            # Basic metrics without psutil
            results['basic'] = self._get_basic_metrics()
        
        # Log file analysis
        results['logs'] = self._analyze_log_files()
        
        # Calculate performance score
        results['performance_score'] = self._calculate_score(results)
        
        # Update metrics
        self.metrics['performance_score'] = results['performance_score']
        if PSUTIL_AVAILABLE:
            self.metrics['cpu_percent'] = results['cpu'].get('percent', 0)
            self.metrics['memory_percent'] = results['memory'].get('percent', 0)
        
        # Track history
        self.performance_history.append({
            'timestamp': results['timestamp'],
            'score': results['performance_score']
        })
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
        
        logger.info(
            f"[{self.name}] Performance Score: {results['performance_score']:.1f}/100"
        )
        
        return results
    
    async def plan(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create plans for performance optimizations.
        
        Args:
            analysis: Results from analyze()
            
        Returns:
            List of improvement plans
        """
        plans = []
        
        # Check CPU
        if analysis.get('cpu', {}).get('percent', 0) > self.thresholds['cpu_warning']:
            plans.append({
                'type': 'high_cpu_alert',
                'priority': 8,
                'description': f"CPU usage is {analysis['cpu']['percent']:.1f}%",
                'metric': 'cpu',
                'value': analysis['cpu']['percent']
            })
        
        # Check memory
        if analysis.get('memory', {}).get('percent', 0) > self.thresholds['memory_warning']:
            plans.append({
                'type': 'high_memory_alert',
                'priority': 8,
                'description': f"Memory usage is {analysis['memory']['percent']:.1f}%",
                'metric': 'memory',
                'value': analysis['memory']['percent']
            })
        
        # Check disk
        if analysis.get('disk', {}).get('percent', 0) > self.thresholds['disk_warning']:
            plans.append({
                'type': 'high_disk_alert',
                'priority': 9,
                'description': f"Disk usage is {analysis['disk']['percent']:.1f}%",
                'metric': 'disk',
                'value': analysis['disk']['percent']
            })
        
        # Check log file sizes
        if analysis.get('logs', {}).get('total_size_mb', 0) > 100:
            plans.append({
                'type': 'log_cleanup',
                'priority': 5,
                'description': 'Log files exceed 100MB, consider cleanup',
                'total_size_mb': analysis['logs']['total_size_mb']
            })
        
        # Save suggestion if performance is low
        if analysis.get('performance_score', 100) < 70:
            self._save_improvement_suggestion({
                'category': 'performance',
                'priority': 7,
                'title': 'Performance Below Threshold',
                'description': f"Performance score is {analysis['performance_score']:.1f}/100",
                'estimated_impact': 0.15,
                'analysis': {
                    'cpu': analysis.get('cpu', {}),
                    'memory': analysis.get('memory', {}),
                    'disk': analysis.get('disk', {})
                }
            })
        
        return plans
    
    async def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a performance improvement plan.
        
        Args:
            plan: An improvement plan
            
        Returns:
            Execution result
        """
        plan_type = plan.get('type', '')
        
        if plan_type in ('high_cpu_alert', 'high_memory_alert', 'high_disk_alert'):
            # Log the alert
            logger.warning(f"[{self.name}] ALERT: {plan['description']}")
            return {
                'status': 'logged',
                'message': f"Performance alert logged: {plan['description']}",
                'action': plan_type
            }
        
        elif plan_type == 'log_cleanup':
            # Just log recommendation (don't auto-delete logs)
            logger.info(f"[{self.name}] Recommendation: {plan['description']}")
            return {
                'status': 'logged',
                'message': 'Log cleanup recommendation logged',
                'action': 'log_cleanup'
            }
        
        else:
            return {
                'status': 'skipped',
                'message': f"Unknown plan type: {plan_type}",
                'action': plan_type
            }
    
    def _get_cpu_metrics(self) -> Dict[str, Any]:
        """Get CPU metrics using psutil."""
        if not PSUTIL_AVAILABLE:
            return {}
        
        try:
            return {
                'percent': psutil.cpu_percent(interval=1),
                'count': psutil.cpu_count(),
                'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
        except Exception as e:
            logger.warning(f"[{self.name}] Error getting CPU metrics: {e}")
            return {'error': str(e)}
    
    def _get_memory_metrics(self) -> Dict[str, Any]:
        """Get memory metrics using psutil."""
        if not PSUTIL_AVAILABLE:
            return {}
        
        try:
            mem = psutil.virtual_memory()
            return {
                'percent': mem.percent,
                'total_gb': round(mem.total / (1024**3), 2),
                'available_gb': round(mem.available / (1024**3), 2),
                'used_gb': round(mem.used / (1024**3), 2)
            }
        except Exception as e:
            logger.warning(f"[{self.name}] Error getting memory metrics: {e}")
            return {'error': str(e)}
    
    def _get_disk_metrics(self) -> Dict[str, Any]:
        """Get disk usage metrics using psutil."""
        if not PSUTIL_AVAILABLE:
            return {}
        
        try:
            disk = psutil.disk_usage('/')
            return {
                'percent': disk.percent,
                'total_gb': round(disk.total / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
                'used_gb': round(disk.used / (1024**3), 2)
            }
        except Exception as e:
            logger.warning(f"[{self.name}] Error getting disk metrics: {e}")
            return {'error': str(e)}
    
    def _get_process_metrics(self) -> Dict[str, Any]:
        """Get process metrics using psutil."""
        if not PSUTIL_AVAILABLE:
            return {}
        
        try:
            current_process = psutil.Process()
            return {
                'pid': current_process.pid,
                'memory_mb': round(current_process.memory_info().rss / (1024**2), 2),
                'cpu_percent': current_process.cpu_percent(interval=0.1),
                'num_threads': current_process.num_threads()
            }
        except Exception as e:
            logger.warning(f"[{self.name}] Error getting process metrics: {e}")
            return {'error': str(e)}
    
    def _get_basic_metrics(self) -> Dict[str, Any]:
        """Get basic metrics without psutil."""
        return {
            'timestamp': datetime.now().isoformat(),
            'load_avg': os.getloadavg() if hasattr(os, 'getloadavg') else None
        }
    
    def _analyze_log_files(self) -> Dict[str, Any]:
        """Analyze log file sizes."""
        log_dirs = [
            Path('logs'),
            Path('logs/autonomous_agents')
        ]
        
        total_size = 0
        file_count = 0
        
        for log_dir in log_dirs:
            if log_dir.exists():
                for log_file in log_dir.rglob('*'):
                    if log_file.is_file():
                        try:
                            total_size += log_file.stat().st_size
                            file_count += 1
                        except:
                            pass
        
        return {
            'total_size_mb': round(total_size / (1024**2), 2),
            'file_count': file_count
        }
    
    def _calculate_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall performance score (0-100)."""
        score = 100.0
        
        if PSUTIL_AVAILABLE:
            # Deduct for high CPU
            cpu_percent = results.get('cpu', {}).get('percent', 0)
            if cpu_percent > 90:
                score -= 30
            elif cpu_percent > 70:
                score -= 15
            elif cpu_percent > 50:
                score -= 5
            
            # Deduct for high memory
            mem_percent = results.get('memory', {}).get('percent', 0)
            if mem_percent > 90:
                score -= 30
            elif mem_percent > 70:
                score -= 15
            elif mem_percent > 50:
                score -= 5
            
            # Deduct for high disk
            disk_percent = results.get('disk', {}).get('percent', 0)
            if disk_percent > 95:
                score -= 20
            elif disk_percent > 85:
                score -= 10
        
        return max(0, min(100, score))
