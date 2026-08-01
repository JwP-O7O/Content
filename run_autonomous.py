#!/usr/bin/env python3
"""Run all autonomous agents - Full system test."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger


async def run_all_agents():
    """Run all autonomous agents and display results."""
    
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║     🤖 AUTONOMOUS IMPROVEMENT SYSTEM - Full Run 🤖      ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
""")
    
    results = {}
    
    # Layer 1: Monitoring
    print("\n" + "=" * 60)
    print("LAYER 1: MONITORING AGENTS")
    print("=" * 60)
    
    try:
        from src.autonomous_agents.monitoring import MonitoringOrchestrator
        orchestrator = MonitoringOrchestrator()
        results['monitoring'] = await orchestrator.run_all_agents()
        print(f"✅ Monitoring complete: {results['monitoring']['aggregate']['overall_score']:.1f}/100")
    except Exception as e:
        print(f"❌ Monitoring failed: {e}")
        results['monitoring'] = {'error': str(e)}
    
    # Execution: Code Fixer
    print("\n" + "=" * 60)
    print("EXECUTION: CODE FIXER")
    print("=" * 60)
    
    try:
        from src.autonomous_agents.execution import CodeFixerAgent
        fixer = CodeFixerAgent()
        results['code_fixer'] = await fixer.run_cycle()
        print(f"✅ Code Fixer complete: {results['code_fixer']['phases']['execute']['executed']} fixes")
    except Exception as e:
        print(f"❌ Code Fixer failed: {e}")
        results['code_fixer'] = {'error': str(e)}
    
    # Specialists
    print("\n" + "=" * 60)
    print("SPECIALISTS")
    print("=" * 60)
    
    # Docstring Generator
    try:
        from src.autonomous_agents.specialists import DocstringGeneratorAgent
        docgen = DocstringGeneratorAgent()
        results['docstring_gen'] = await docgen.run_cycle()
        coverage = results['docstring_gen']['phases']['analyze']['result'].get('coverage', 0)
        print(f"✅ Docstring Generator: {coverage:.1f}% coverage")
    except Exception as e:
        print(f"❌ Docstring Generator failed: {e}")
        results['docstring_gen'] = {'error': str(e)}
    
    # Agent Validator
    try:
        from src.autonomous_agents.specialists import AgentValidatorAgent
        validator = AgentValidatorAgent()
        results['agent_validator'] = await validator.run_cycle()
        valid_rate = results['agent_validator']['phases']['analyze']['result'].get('validity_rate', 0)
        print(f"✅ Agent Validator: {valid_rate:.1f}% valid")
    except Exception as e:
        print(f"❌ Agent Validator failed: {e}")
        results['agent_validator'] = {'error': str(e)}
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    monitoring = results.get('monitoring', {})
    if 'aggregate' in monitoring:
        scores = monitoring['aggregate'].get('scores', {})
        print(f"\n📊 System Health Scores:")
        print(f"   Code Health:    {scores.get('code_health', 0):.1f}/100")
        print(f"   Performance:    {scores.get('performance', 0):.1f}/100")
        print(f"   Security:       {scores.get('security', 0):.1f}/100")
        print(f"   Dependencies:   {scores.get('dependencies', 0):.1f}/100")
        print(f"   Overall:        {monitoring['aggregate'].get('overall_score', 0):.1f}/100")
    
    # Count improvements
    total_improvements = 0
    for key, result in results.items():
        if isinstance(result, dict) and 'phases' in result:
            executed = result.get('phases', {}).get('execute', {}).get('executed', 0)
            total_improvements += executed
    
    print(f"\n🔧 Total Improvements Applied: {total_improvements}")
    print(f"📁 Logs saved to: logs/autonomous_agents/")
    print(f"📝 Suggestions saved to: data/improvement_plans/")
    
    print("\n" + "=" * 60)
    print("✅ AUTONOMOUS SYSTEM RUN COMPLETE")
    print("=" * 60)
    
    return results


async def run_quick():
    """Quick run - just monitoring."""
    from src.autonomous_agents.monitoring import MonitoringOrchestrator
    orchestrator = MonitoringOrchestrator()
    return await orchestrator.run_all_agents()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Autonomous Improvement System')
    parser.add_argument('--quick', '-q', action='store_true', help='Quick run (monitoring only)')
    parser.add_argument('--agent', '-a', type=str, help='Run specific agent')
    args = parser.parse_args()
    
    if args.quick:
        results = asyncio.run(run_quick())
        print(f"\nOverall: {results['aggregate']['overall_score']:.1f}/100")
    elif args.agent:
        print(f"Running agent: {args.agent}")
        # TODO: Add specific agent running
    else:
        asyncio.run(run_all_agents())
