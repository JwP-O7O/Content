#!/usr/bin/env python3
"""Run the monitoring agents - Layer 1 of the Autonomous Improvement System."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger


async def main():
    """Run monitoring cycle and display results."""
    
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║     Layer 1: Monitoring Agents - Running Cycle          ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
""")
    
    try:
        from src.autonomous_agents.monitoring import MonitoringOrchestrator
        
        orchestrator = MonitoringOrchestrator()
        results = await orchestrator.run_all_agents()
        
        # Display results
        print("\n" + "=" * 60)
        print("MONITORING RESULTS")
        print("=" * 60)
        
        aggregate = results.get('aggregate', {})
        scores = aggregate.get('scores', {})
        
        print(f"\n📊 Individual Scores:")
        print(f"   Code Health:    {scores.get('code_health', 0):.1f}/100")
        print(f"   Performance:    {scores.get('performance', 0):.1f}/100")
        print(f"   Security:       {scores.get('security', 0):.1f}/100")
        print(f"   Dependencies:   {scores.get('dependencies', 0):.1f}/100")
        
        print(f"\n🎯 Overall Score:  {aggregate.get('overall_score', 0):.1f}/100")
        print(f"   Status:         {aggregate.get('status', 'unknown').upper()}")
        
        print(f"\n⏱️  Duration:       {results.get('duration_seconds', 0):.2f} seconds")
        
        # Show improvements logged
        print(f"\n📁 Results saved to: logs/autonomous_agents/orchestrator/")
        
        print("\n" + "=" * 60)
        
        return results
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        print(f"\n❌ Error: Could not import monitoring agents: {e}")
        print("   Make sure all dependencies are installed.")
        return None
    except Exception as e:
        logger.error(f"Error running monitoring: {e}")
        print(f"\n❌ Error: {e}")
        return None


if __name__ == "__main__":
    results = asyncio.run(main())
    
    if results:
        status = results.get('aggregate', {}).get('status', 'unknown')
        if status == 'healthy':
            print("\n✅ System is healthy!")
        elif status == 'warning':
            print("\n⚠️  System has some issues that need attention.")
        else:
            print("\n🚨 System requires immediate attention!")
