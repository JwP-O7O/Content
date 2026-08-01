#!/usr/bin/env python3
"""Dashboard for Autonomous Improvement System - View monitoring results."""

import json
from datetime import datetime
from pathlib import Path

from loguru import logger


class Dashboard:
    """Simple text-based dashboard for monitoring results."""
    
    def __init__(self):
        self.logs_dir = Path("logs/autonomous_agents")
        self.data_dir = Path("data/improvement_plans")
    
    def show(self):
        """Display the dashboard."""
        self._clear()
        self._print_header()
        self._print_latest_monitoring()
        self._print_recent_improvements()
        self._print_pending_suggestions()
        self._print_agent_stats()
    
    def _clear(self):
        """Clear screen."""
        print("\033[2J\033[H", end="")
    
    def _print_header(self):
        """Print dashboard header."""
        print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     🤖 AUTONOMOUS IMPROVEMENT SYSTEM - DASHBOARD 🤖             ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
        print(f"  📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    def _print_latest_monitoring(self):
        """Print latest monitoring results."""
        print("═" * 66)
        print("📊 LATEST MONITORING RESULTS")
        print("═" * 66)
        
        orchestrator_dir = self.logs_dir / "orchestrator"
        if not orchestrator_dir.exists():
            print("  No monitoring data available yet.")
            print()
            return
        
        # Get latest file
        files = sorted(orchestrator_dir.glob("monitoring_*.json"), reverse=True)
        if not files:
            print("  No monitoring data available yet.")
            print()
            return
        
        try:
            with open(files[0]) as f:
                data = json.load(f)
            
            aggregate = data.get('aggregate', {})
            scores = aggregate.get('scores', {})
            
            print(f"\n  Last run: {data.get('completed_at', 'unknown')[:19]}")
            print(f"  Duration: {data.get('duration_seconds', 0):.1f}s")
            print()
            
            # Score bars
            self._print_score_bar("Code Health", scores.get('code_health', 0))
            self._print_score_bar("Performance", scores.get('performance', 0))
            self._print_score_bar("Security", scores.get('security', 0))
            self._print_score_bar("Dependencies", scores.get('dependencies', 0))
            print()
            self._print_score_bar("OVERALL", aggregate.get('overall_score', 0), highlight=True)
            
        except Exception as e:
            print(f"  Error loading data: {e}")
        
        print()
    
    def _print_score_bar(self, label: str, score: float, highlight: bool = False):
        """Print a score bar."""
        bar_width = 30
        filled = int(score / 100 * bar_width)
        empty = bar_width - filled
        
        # Color based on score
        if score >= 80:
            color = "\033[92m"  # Green
        elif score >= 60:
            color = "\033[93m"  # Yellow
        else:
            color = "\033[91m"  # Red
        
        reset = "\033[0m"
        bold = "\033[1m" if highlight else ""
        
        bar = f"{color}{'█' * filled}{'░' * empty}{reset}"
        print(f"  {bold}{label:15}{reset} [{bar}] {bold}{score:5.1f}/100{reset}")
    
    def _print_recent_improvements(self):
        """Print recent improvements."""
        print("═" * 66)
        print("🔧 RECENT IMPROVEMENTS")
        print("═" * 66)
        
        # Check agent logs
        count = 0
        for agent_dir in self.logs_dir.iterdir():
            if agent_dir.is_dir() and agent_dir.name != "orchestrator":
                for log_file in sorted(agent_dir.glob("*.jsonl"), reverse=True)[:1]:
                    try:
                        with open(log_file) as f:
                            for line in f:
                                if line.strip():
                                    entry = json.loads(line)
                                    if entry.get('phases', {}).get('execute', {}).get('executed', 0) > 0:
                                        count += entry['phases']['execute']['executed']
                    except:
                        pass
        
        print(f"\n  Total improvements applied today: {count}")
        print()
    
    def _print_pending_suggestions(self):
        """Print pending improvement suggestions."""
        print("═" * 66)
        print("📝 PENDING SUGGESTIONS")
        print("═" * 66)
        
        suggestions = []
        
        for layer_dir in self.data_dir.iterdir():
            if layer_dir.is_dir():
                for suggestion_file in layer_dir.glob("*.jsonl"):
                    try:
                        with open(suggestion_file) as f:
                            for line in f:
                                if line.strip():
                                    suggestions.append(json.loads(line))
                    except:
                        pass
        
        # Sort by priority
        suggestions.sort(key=lambda x: x.get('priority', 0), reverse=True)
        
        if not suggestions:
            print("\n  No pending suggestions.")
        else:
            print(f"\n  {len(suggestions)} suggestions pending:\n")
            for s in suggestions[:5]:
                priority = s.get('priority', 0)
                icon = "🔴" if priority >= 8 else "🟡" if priority >= 5 else "🟢"
                print(f"  {icon} [{priority}] {s.get('title', 'Unknown')}")
                print(f"      {s.get('description', '')[:50]}...")
                print()
        
        print()
    
    def _print_agent_stats(self):
        """Print agent statistics."""
        print("═" * 66)
        print("🤖 AGENT STATUS")
        print("═" * 66)
        
        agents = [
            ("Monitoring", ["CodeHealthMonitor", "PerformanceMonitor", "SecurityAuditor", "DependencyScanner"]),
            ("Analysis", ["CodeQualityAnalyzer", "ArchitectureAnalyzer", "TestCoverageAnalyzer", "DocumentationAnalyzer"]),
            ("Execution", ["CodeFixerAgent"]),
            ("Specialists", ["DocstringGeneratorAgent", "TestGeneratorAgent", "AgentValidatorAgent", "TypeHintAgent", "QueryOptimizerAgent"]),
        ]
        
        print()
        for category, agent_list in agents:
            print(f"  {category}:")
            for agent in agent_list:
                agent_lower = agent.lower().replace('agent', '')
                log_dir = self.logs_dir / agent_lower
                
                if log_dir.exists():
                    status = "✅"
                else:
                    # Check if any log exists
                    status = "⬚"
                
                print(f"    {status} {agent}")
            print()
        
        print("═" * 66)
        print("  Commands:")
        print("    python3 run_monitoring.py      - Quick monitoring run")
        print("    python3 run_autonomous.py      - Full system run")
        print("    python3 -m src.autonomous_agents.scheduler  - Start scheduler")
        print("═" * 66)


def main():
    """Run the dashboard."""
    dashboard = Dashboard()
    dashboard.show()


if __name__ == "__main__":
    main()
