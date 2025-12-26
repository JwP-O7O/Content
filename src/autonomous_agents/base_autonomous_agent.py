"""Base class for all autonomous improvement agents."""

import asyncio
import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger


class BaseAutonomousAgent(ABC):
    """
    Base class for all autonomous improvement agents.
    
    These agents operate independently to monitor, analyze, plan,
    and execute improvements to the system.
    
    Implements a file-based logging system that works without a database.
    """
    
    def __init__(self, name: str, layer: str, interval_seconds: int = 3600):
        """
        Initialize autonomous agent.
        
        Args:
            name: Agent name (e.g., "CodeHealthMonitor")
            layer: Which layer this agent belongs to (e.g., "monitoring")
            interval_seconds: How often to run (default: 1 hour)
        """
        self.name = name
        self.layer = layer
        self.interval_seconds = interval_seconds
        self.running = False
        self.metrics: Dict[str, Any] = {}
        self.last_run: Optional[datetime] = None
        
        # Setup log directories
        self.log_dir = Path("logs/autonomous_agents") / name.lower()
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.data_dir = Path("data/improvement_plans") / layer
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"[{self.name}] Initialized (layer: {layer}, interval: {interval_seconds}s)")
    
    @abstractmethod
    async def analyze(self) -> Dict[str, Any]:
        """
        Analyze current state and identify issues/opportunities.
        
        Returns:
            Dictionary with analysis results including issues found
        """
        pass
    
    @abstractmethod
    async def plan(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Create improvement plans based on analysis.
        
        Args:
            analysis: Results from analyze()
            
        Returns:
            List of improvement plans to execute
        """
        pass
    
    @abstractmethod
    async def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an improvement plan.
        
        Args:
            plan: A single improvement plan from plan()
            
        Returns:
            Dictionary with execution results
        """
        pass
    
    async def validate(self, result: Dict[str, Any]) -> bool:
        """
        Validate that changes were successful.
        
        Args:
            result: Results from execute()
            
        Returns:
            True if successful, False otherwise
        """
        return result.get('status') in ('success', 'partial', 'logged')
    
    async def learn(self, result: Dict[str, Any]):
        """
        Learn from execution results to improve future performance.
        
        Args:
            result: Results from execute()
        """
        # Store successful patterns for future reference
        if result.get('status') == 'success':
            self._save_learned_pattern({
                'timestamp': datetime.now().isoformat(),
                'agent': self.name,
                'action': result.get('action', 'unknown'),
                'outcome': 'success'
            })
    
    async def run_cycle(self) -> Dict[str, Any]:
        """
        Run a complete improvement cycle: analyze → plan → execute → validate → learn.
        
        Returns:
            Dictionary with cycle results
        """
        logger.info(f"[{self.name}] Starting improvement cycle")
        cycle_start = datetime.now()
        
        cycle_result = {
            'agent': self.name,
            'layer': self.layer,
            'started_at': cycle_start.isoformat(),
            'status': 'running',
            'phases': {}
        }
        
        try:
            # Phase 1: Analyze
            logger.info(f"[{self.name}] Phase 1: Analyzing...")
            analysis = await self.analyze()
            cycle_result['phases']['analyze'] = {
                'status': 'success',
                'result': analysis
            }
            self._log_activity('analyze', 'success', analysis)
            
            # Phase 2: Plan
            logger.info(f"[{self.name}] Phase 2: Planning...")
            plans = await self.plan(analysis)
            cycle_result['phases']['plan'] = {
                'status': 'success',
                'plans_created': len(plans)
            }
            self._log_activity('plan', 'success', {'plans_created': len(plans)})
            
            # Phase 3: Execute each plan
            logger.info(f"[{self.name}] Phase 3: Executing {len(plans)} plans...")
            execution_results = []
            
            for i, plan in enumerate(plans, 1):
                logger.info(f"[{self.name}] Executing plan {i}/{len(plans)}: {plan.get('type', 'unknown')}")
                
                try:
                    result = await self.execute(plan)
                    result['plan'] = plan
                    
                    # Phase 4: Validate
                    is_valid = await self.validate(result)
                    result['validated'] = is_valid
                    
                    if is_valid:
                        # Phase 5: Learn
                        await self.learn(result)
                        execution_results.append(result)
                        self._log_activity('execute', 'success', result)
                    else:
                        self._log_activity('execute', 'validation_failed', result)
                        
                except Exception as e:
                    logger.error(f"[{self.name}] Failed to execute plan: {e}")
                    self._log_activity('execute', 'error', {'error': str(e), 'plan': plan})
            
            cycle_result['phases']['execute'] = {
                'status': 'success',
                'executed': len(execution_results),
                'results': execution_results
            }
            
            # Cycle complete
            cycle_end = datetime.now()
            cycle_result['status'] = 'success'
            cycle_result['completed_at'] = cycle_end.isoformat()
            cycle_result['duration_seconds'] = (cycle_end - cycle_start).total_seconds()
            
            self.last_run = cycle_end
            
            logger.info(
                f"[{self.name}] Cycle complete: "
                f"{len(execution_results)} improvements in "
                f"{cycle_result['duration_seconds']:.2f}s"
            )
            
            # Save cycle result
            self._save_cycle_result(cycle_result)
            
        except Exception as e:
            logger.error(f"[{self.name}] Cycle failed: {e}")
            cycle_result['status'] = 'error'
            cycle_result['error'] = str(e)
            self._log_activity('cycle', 'error', {'error': str(e)})
        
        return cycle_result
    
    async def start(self):
        """Start the autonomous agent loop (runs continuously)."""
        self.running = True
        logger.info(f"[{self.name}] Starting autonomous operation")
        
        while self.running:
            try:
                await self.run_cycle()
            except Exception as e:
                logger.error(f"[{self.name}] Error in cycle: {e}")
            
            if self.running:
                logger.info(f"[{self.name}] Sleeping for {self.interval_seconds}s...")
                await asyncio.sleep(self.interval_seconds)
    
    def stop(self):
        """Stop the autonomous agent."""
        self.running = False
        logger.info(f"[{self.name}] Stopping")
    
    def _log_activity(self, action: str, status: str, details: Dict[str, Any]):
        """
        Log agent activity to JSON file.
        
        Args:
            action: What action was performed
            status: success, error, etc.
            details: Additional details
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'agent': self.name,
            'layer': self.layer,
            'action': action,
            'status': status,
            'details': details,
            'metrics': self.metrics
        }
        
        # Write to daily log file
        log_file = self.log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.warning(f"[{self.name}] Failed to write log: {e}")
    
    def _save_cycle_result(self, result: Dict[str, Any]):
        """Save complete cycle result to file."""
        result_file = self.log_dir / f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"[{self.name}] Failed to save cycle result: {e}")
    
    def _save_learned_pattern(self, pattern: Dict[str, Any]):
        """Save a learned pattern for future use."""
        patterns_file = self.data_dir / f"{self.name.lower()}_patterns.jsonl"
        
        try:
            with open(patterns_file, 'a') as f:
                f.write(json.dumps(pattern) + '\n')
        except Exception as e:
            logger.warning(f"[{self.name}] Failed to save pattern: {e}")
    
    def _save_improvement_suggestion(self, suggestion: Dict[str, Any]):
        """Save an improvement suggestion."""
        suggestion['agent'] = self.name
        suggestion['layer'] = self.layer
        suggestion['created_at'] = datetime.now().isoformat()
        suggestion['status'] = suggestion.get('status', 'pending')
        
        suggestions_file = self.data_dir / "improvement_suggestions.jsonl"
        
        try:
            with open(suggestions_file, 'a') as f:
                f.write(json.dumps(suggestion) + '\n')
        except Exception as e:
            logger.warning(f"[{self.name}] Failed to save suggestion: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            'name': self.name,
            'layer': self.layer,
            'running': self.running,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'interval_seconds': self.interval_seconds,
            'metrics': self.metrics
        }
