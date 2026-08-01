"""Autonomous System Scheduler - Continuous improvement via APScheduler."""

import asyncio
import signal
import sys
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
)
logger.add("logs/autonomous_scheduler.log", rotation="1 day", retention="7 days")


class AutonomousScheduler:
    """
    Schedules and runs autonomous agents continuously.

    Default intervals:
    - Monitoring: every 30 minutes
    - Code fixes: every 1 hour
    - Analysis: every 6 hours
    - Specialists: every 6 hours
    - Full system report: daily
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.stats = {"runs": 0, "improvements": 0, "started_at": None}

    async def run_monitoring(self):
        """Run monitoring agents."""
        logger.info("=" * 50)
        logger.info("SCHEDULED: Monitoring Agents")
        logger.info("=" * 50)

        try:
            from src.autonomous_agents.monitoring import MonitoringOrchestrator

            orchestrator = MonitoringOrchestrator()
            results = await orchestrator.run_all_agents()

            score = results.get("aggregate", {}).get("overall_score", 0)
            self.stats["runs"] += 1

            logger.info(f"Monitoring complete: {score:.1f}/100")

            return results

        except Exception as e:
            logger.error(f"Monitoring failed: {e}")
            return {"error": str(e)}

    async def run_code_fixer(self):
        """Run code fixer agent."""
        logger.info("=" * 50)
        logger.info("SCHEDULED: Code Fixer")
        logger.info("=" * 50)

        try:
            from src.autonomous_agents.execution import CodeFixerAgent

            agent = CodeFixerAgent()
            result = await agent.run_cycle()

            executed = result.get("phases", {}).get("execute", {}).get("executed", 0)
            self.stats["improvements"] += executed

            logger.info(f"Code fixer complete: {executed} improvements")

            return result

        except Exception as e:
            logger.error(f"Code fixer failed: {e}")
            return {"error": str(e)}

    async def run_analysis(self):
        """Run analysis agents."""
        logger.info("=" * 50)
        logger.info("SCHEDULED: Analysis Agents")
        logger.info("=" * 50)

        try:
            from src.autonomous_agents.analysis import (
                ArchitectureAnalyzer,
                CodeQualityAnalyzer,
                DocumentationAnalyzer,
                TestCoverageAnalyzer,
            )

            results = {}

            for AgentClass in [
                CodeQualityAnalyzer,
                ArchitectureAnalyzer,
                TestCoverageAnalyzer,
                DocumentationAnalyzer,
            ]:
                try:
                    agent = AgentClass()
                    results[agent.name] = await agent.run_cycle()
                except Exception as e:
                    logger.warning(f"{AgentClass.__name__} failed: {e}")
                    results[AgentClass.__name__] = {"error": str(e)}

            logger.info(f"Analysis complete: {len(results)} agents run")
            return results

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {"error": str(e)}

    async def run_specialists(self):
        """Run specialist agents."""
        logger.info("=" * 50)
        logger.info("SCHEDULED: Specialist Agents")
        logger.info("=" * 50)

        try:
            from src.autonomous_agents.specialists import (
                AgentValidatorAgent,
                DocstringGeneratorAgent,
                QueryOptimizerAgent,
                TestGeneratorAgent,
                TypeHintAgent,
            )

            results = {}

            for AgentClass in [
                DocstringGeneratorAgent,
                AgentValidatorAgent,
                TypeHintAgent,
                QueryOptimizerAgent,
                TestGeneratorAgent,
            ]:
                try:
                    agent = AgentClass()
                    results[agent.name] = await agent.run_cycle()
                except Exception as e:
                    logger.warning(f"{AgentClass.__name__} failed: {e}")
                    results[AgentClass.__name__] = {"error": str(e)}

            logger.info(f"Specialists complete: {len(results)} agents run")

            return results

        except Exception as e:
            logger.error(f"Specialists failed: {e}")
            return {"error": str(e)}

    async def generate_report(self):
        """Generate daily summary report."""
        logger.info("=" * 50)
        logger.info("SCHEDULED: Daily Report")
        logger.info("=" * 50)

        report = {
            "date": datetime.now().isoformat(),
            "uptime": str(datetime.now() - self.stats["started_at"])
            if self.stats["started_at"]
            else "N/A",
            "total_runs": self.stats["runs"],
            "total_improvements": self.stats["improvements"],
        }

        # Save report
        reports_dir = Path("logs/autonomous_agents/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)

        report_file = reports_dir / f"daily_{datetime.now().strftime('%Y%m%d')}.json"

        import json

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Daily report saved: {report_file}")
        logger.info(f"  Total runs: {report['total_runs']}")
        logger.info(f"  Total improvements: {report['total_improvements']}")

        return report

    def start(self):
        """Start the scheduler."""
        if self.is_running:
            logger.warning("Scheduler already running")
            return

        self.stats["started_at"] = datetime.now()

        # Add jobs
        self.scheduler.add_job(
            self.run_monitoring,
            IntervalTrigger(minutes=30),
            id="monitoring",
            name="Monitoring Agents",
        )

        self.scheduler.add_job(
            self.run_code_fixer, IntervalTrigger(hours=1), id="code_fixer", name="Code Fixer"
        )

        self.scheduler.add_job(
            self.run_analysis,
            IntervalTrigger(hours=6),
            id="analysis",
            name="Analysis Agents",
        )

        self.scheduler.add_job(
            self.run_specialists,
            IntervalTrigger(hours=6),
            id="specialists",
            name="Specialist Agents",
        )

        self.scheduler.add_job(
            self.generate_report, IntervalTrigger(hours=24), id="daily_report", name="Daily Report"
        )

        self.scheduler.start()
        self.is_running = True

        logger.info("=" * 60)
        logger.info("🤖 AUTONOMOUS SCHEDULER STARTED")
        logger.info("=" * 60)
        logger.info("Scheduled jobs:")
        logger.info("  - Monitoring: every 30 minutes")
        logger.info("  - Code fixer: every 1 hour")
        logger.info("  - Analysis: every 6 hours")
        logger.info("  - Specialists: every 6 hours")
        logger.info("  - Daily report: every 24 hours")
        logger.info("=" * 60)

    def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            return

        self.scheduler.shutdown()
        self.is_running = False
        logger.info("Scheduler stopped")

    async def run_initial(self):
        """Run all agents once at startup."""
        logger.info("Running initial checks...")
        await self.run_monitoring()
        # Skipped heavy operations for initial run to ensure quick startup
        # await self.run_analysis()
        # await self.run_code_fixer()


async def main():
    """Main entry point for the scheduler."""
    scheduler = AutonomousScheduler()

    # Handle shutdown
    def shutdown(signum, frame):
        logger.info("Shutdown signal received")
        scheduler.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Run initial checks
    await scheduler.run_initial()

    # Start scheduler
    scheduler.start()

    # Keep running
    try:
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())
