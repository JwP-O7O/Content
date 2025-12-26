"""MonitoringOrchestrator - Coordinates all monitoring agents."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from .code_health_monitor import CodeHealthMonitor
from .performance_monitor import PerformanceMonitor
from .security_auditor import SecurityAuditor
from .dependency_scanner import DependencyScanner


class MonitoringOrchestrator:
    """
    Coordinates all Layer 1 monitoring agents.
    
    Provides:
    - Centralized agent management
    - Aggregated status reporting
    - Sequential or parallel execution
    - Health score aggregation
    """
    
    def __init__(self):
        """Initialize the monitoring orchestrator with all agents."""
        logger.info("Initializing Monitoring Orchestrator")
        
        self.agents = {
            'code_health': CodeHealthMonitor(),
            'performance': PerformanceMonitor(),
            'security': SecurityAuditor(),
            'dependencies': DependencyScanner()
        }
        
        self.last_run: Optional[datetime] = None
        self.results_dir = Path("logs/autonomous_agents/orchestrator")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Monitoring Orchestrator ready with {len(self.agents)} agents")
    
    async def run_all_agents(self, parallel: bool = False) -> Dict[str, Any]:
        """
        Run all monitoring agents.
        
        Args:
            parallel: If True, run agents in parallel; otherwise sequential
            
        Returns:
            Aggregated results from all agents
        """
        logger.info("=" * 60)
        logger.info("MONITORING ORCHESTRATOR: Starting all agents")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        results = {
            'started_at': start_time.isoformat(),
            'mode': 'parallel' if parallel else 'sequential',
            'agents': {}
        }
        
        if parallel:
            # Run all agents in parallel
            tasks = [
                self._run_agent_safe(name, agent)
                for name, agent in self.agents.items()
            ]
            agent_results = await asyncio.gather(*tasks)
            
            for (name, _), result in zip(self.agents.items(), agent_results):
                results['agents'][name] = result
        else:
            # Run agents sequentially
            for name, agent in self.agents.items():
                results['agents'][name] = await self._run_agent_safe(name, agent)
        
        # Calculate aggregate scores
        results['aggregate'] = self._calculate_aggregate_scores(results['agents'])
        
        # Completion
        end_time = datetime.now()
        results['completed_at'] = end_time.isoformat()
        results['duration_seconds'] = (end_time - start_time).total_seconds()
        
        self.last_run = end_time
        
        # Save results
        self._save_results(results)
        
        # Log summary
        logger.info("=" * 60)
        logger.info("MONITORING ORCHESTRATOR: Complete")
        logger.info(f"  Duration: {results['duration_seconds']:.2f}s")
        logger.info(f"  Overall Health: {results['aggregate']['overall_score']:.1f}/100")
        logger.info("=" * 60)
        
        return results
    
    async def _run_agent_safe(self, name: str, agent) -> Dict[str, Any]:
        """
        Run a single agent with error handling.
        
        Args:
            name: Agent name
            agent: Agent instance
            
        Returns:
            Agent results or error info
        """
        try:
            logger.info(f"Running agent: {name}")
            result = await agent.run_cycle()
            return {
                'status': 'success',
                'result': result
            }
        except Exception as e:
            logger.error(f"Agent {name} failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _calculate_aggregate_scores(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate aggregate scores from all agent results.
        
        Args:
            agent_results: Results from all agents
            
        Returns:
            Aggregate metrics
        """
        scores = {
            'code_health': 0,
            'performance': 0,
            'security': 0,
            'dependencies': 0
        }
        
        # Extract scores from results
        for name, data in agent_results.items():
            if data.get('status') == 'success':
                result = data.get('result', {})
                phases = result.get('phases', {})
                analyze = phases.get('analyze', {}).get('result', {})
                
                if name == 'code_health':
                    scores['code_health'] = analyze.get('health_score', 0)
                elif name == 'performance':
                    scores['performance'] = analyze.get('performance_score', 0)
                elif name == 'security':
                    scores['security'] = analyze.get('security_score', 0)
                elif name == 'dependencies':
                    scores['dependencies'] = analyze.get('freshness_score', 0)
        
        # Calculate overall (weighted average)
        weights = {
            'code_health': 0.3,
            'performance': 0.2,
            'security': 0.35,  # Security is most important
            'dependencies': 0.15
        }
        
        overall = sum(scores[k] * weights[k] for k in scores)
        
        return {
            'scores': scores,
            'overall_score': round(overall, 1),
            'status': 'healthy' if overall >= 80 else 'warning' if overall >= 60 else 'critical'
        }
    
    def _save_results(self, results: Dict[str, Any]):
        """Save orchestrator results to file."""
        filename = f"monitoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.results_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Results saved to {filepath}")
        except Exception as e:
            logger.warning(f"Failed to save results: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of all agents."""
        return {
            'orchestrator': 'ready',
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'agents': {
                name: agent.get_status()
                for name, agent in self.agents.items()
            }
        }
    
    def get_latest_results(self) -> Optional[Dict[str, Any]]:
        """Get the most recent orchestrator results."""
        try:
            files = sorted(self.results_dir.glob('monitoring_*.json'), reverse=True)
            if files:
                with open(files[0]) as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading latest results: {e}")
        return None


async def run_monitoring_cycle():
    """
    Convenience function to run a single monitoring cycle.
    
    Returns:
        Orchestrator results
    """
    orchestrator = MonitoringOrchestrator()
    return await orchestrator.run_all_agents()


if __name__ == "__main__":
    # Run monitoring cycle when executed directly
    import asyncio
    
    async def main():
        results = await run_monitoring_cycle()
        print(f"\nOverall Health: {results['aggregate']['overall_score']}/100")
        print(f"Status: {results['aggregate']['status']}")
    
    asyncio.run(main())
