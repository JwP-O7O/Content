"""Scheduler for running agents periodically."""

import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from src.orchestrator import AgentOrchestrator
from src.utils.logger import setup_logger


class ContentCreatorScheduler:
    """
    Scheduler for the Content Creator system.

    Manages periodic execution of the agent pipeline.
    """

    def __init__(self, phase: int = 4):
        """
        Initialize the scheduler.

        Args:
            phase: Which phase to run (1, 2, 3, or 4). Each phase includes all previous phases + new agents.
        """
        setup_logger()
        logger.info(f"Initializing Content Creator Scheduler (Phase {phase})...")

        self.scheduler = AsyncIOScheduler()
        self.orchestrator = AgentOrchestrator()
        self.phase = phase

        self._setup_jobs()

    def _setup_jobs(self):
        """Set up scheduled jobs based on phase."""

        # Market scanning - every 30 minutes
        self.scheduler.add_job(
            self.orchestrator.run_market_scan_only,
            trigger=IntervalTrigger(minutes=30),
            id="market_scan",
            name="Market Scanner",
            replace_existing=True
        )

        # Full analysis pipeline - every 2 hours
        self.scheduler.add_job(
            self._run_analysis_pipeline,
            trigger=IntervalTrigger(hours=2),
            id="analysis_pipeline",
            name="Analysis Pipeline",
            replace_existing=True
        )

        # Content creation - every 3 hours
        self.scheduler.add_job(
            self.orchestrator.run_content_creation_pipeline,
            trigger=IntervalTrigger(hours=3),
            id="content_creation",
            name="Content Creation",
            replace_existing=True
        )

        if self.phase >= 4:
            # Phase 4 jobs (includes all Phase 3 jobs)

            # Engagement - every hour
            self.scheduler.add_job(
                self.orchestrator.run_engagement_pipeline,
                trigger=IntervalTrigger(hours=1),
                id="engagement",
                name="Engagement Pipeline",
                replace_existing=True
            )

            # Analytics collection - every 6 hours
            self.scheduler.add_job(
                self.orchestrator.analytics_agent.run,
                trigger=IntervalTrigger(hours=6),
                id="analytics",
                name="Analytics Collection",
                replace_existing=True
            )

            # Content repurposing - daily at 10 AM UTC
            self.scheduler.add_job(
                self.orchestrator.content_strategist.plan_content_repurposing,
                trigger=CronTrigger(hour=10, minute=0),
                id="content_repurposing",
                name="Content Repurposing",
                replace_existing=True
            )

            # Conversion - every 4 hours
            self.scheduler.add_job(
                self.orchestrator.conversion_agent.run,
                trigger=IntervalTrigger(hours=4),
                id="conversion",
                name="User Conversion",
                replace_existing=True
            )

            # Onboarding - every 2 hours
            self.scheduler.add_job(
                self.orchestrator.onboarding_agent.run,
                trigger=IntervalTrigger(hours=2),
                id="onboarding",
                name="Member Onboarding",
                replace_existing=True
            )

            # Exclusive content - every 3 hours
            self.scheduler.add_job(
                self.orchestrator.exclusive_content_agent.run,
                trigger=IntervalTrigger(hours=3),
                id="exclusive_content",
                name="Exclusive Content",
                replace_existing=True
            )

            # Community moderation - every 30 minutes
            self.scheduler.add_job(
                self.orchestrator.community_moderator.run,
                trigger=IntervalTrigger(minutes=30),
                id="moderation",
                name="Community Moderation",
                replace_existing=True
            )

            # Performance Analytics - every 12 hours
            self.scheduler.add_job(
                self.orchestrator.performance_analytics.run,
                trigger=IntervalTrigger(hours=12),
                id="performance_analytics",
                name="Performance Analytics",
                replace_existing=True
            )

            # A/B Testing - every 8 hours
            self.scheduler.add_job(
                self.orchestrator.ab_testing.run,
                trigger=IntervalTrigger(hours=8),
                id="ab_testing",
                name="A/B Testing",
                replace_existing=True
            )

            # Strategy Tuning - daily at 2 AM UTC
            self.scheduler.add_job(
                self.orchestrator.strategy_tuning.run,
                trigger=CronTrigger(hour=2, minute=0),
                id="strategy_tuning",
                name="Strategy Tuning",
                replace_existing=True
            )

            # Feedback Loop - daily at 4 AM UTC (after strategy tuning)
            self.scheduler.add_job(
                self.orchestrator.feedback_loop.run,
                trigger=CronTrigger(hour=4, minute=0),
                id="feedback_loop",
                name="Feedback Loop Coordination",
                replace_existing=True
            )

            # Full Phase 4 pipeline - daily at 6 AM UTC
            self.scheduler.add_job(
                self.orchestrator.run_full_pipeline_phase4,
                trigger=CronTrigger(hour=6, minute=0),
                id="daily_full_pipeline",
                name="Daily Full Pipeline (Phase 4)",
                replace_existing=True
            )

            logger.info("Scheduled jobs configured (Phase 4):")
            logger.info("  - Market Scan: Every 30 minutes")
            logger.info("  - Analysis: Every 2 hours")
            logger.info("  - Content Creation: Every 3 hours")
            logger.info("  - Engagement: Every hour")
            logger.info("  - Analytics: Every 6 hours")
            logger.info("  - Content Repurposing: Daily at 10 AM UTC")
            logger.info("  - Conversion: Every 4 hours")
            logger.info("  - Onboarding: Every 2 hours")
            logger.info("  - Exclusive Content: Every 3 hours")
            logger.info("  - Moderation: Every 30 minutes")
            logger.info("  - Performance Analytics: Every 12 hours")
            logger.info("  - A/B Testing: Every 8 hours")
            logger.info("  - Strategy Tuning: Daily at 2 AM UTC")
            logger.info("  - Feedback Loop: Daily at 4 AM UTC")
            logger.info("  - Full Phase 4 Pipeline: Daily at 6 AM UTC")

        elif self.phase >= 3:
            # Phase 3 jobs (includes all Phase 2 jobs)

            # Engagement - every hour
            self.scheduler.add_job(
                self.orchestrator.run_engagement_pipeline,
                trigger=IntervalTrigger(hours=1),
                id="engagement",
                name="Engagement Pipeline",
                replace_existing=True
            )

            # Analytics collection - every 6 hours
            self.scheduler.add_job(
                self.orchestrator.analytics_agent.run,
                trigger=IntervalTrigger(hours=6),
                id="analytics",
                name="Analytics Collection",
                replace_existing=True
            )

            # Content repurposing - daily at 10 AM UTC
            self.scheduler.add_job(
                self.orchestrator.content_strategist.plan_content_repurposing,
                trigger=CronTrigger(hour=10, minute=0),
                id="content_repurposing",
                name="Content Repurposing",
                replace_existing=True
            )

            # Conversion - every 4 hours
            self.scheduler.add_job(
                self.orchestrator.conversion_agent.run,
                trigger=IntervalTrigger(hours=4),
                id="conversion",
                name="User Conversion",
                replace_existing=True
            )

            # Onboarding - every 2 hours
            self.scheduler.add_job(
                self.orchestrator.onboarding_agent.run,
                trigger=IntervalTrigger(hours=2),
                id="onboarding",
                name="Member Onboarding",
                replace_existing=True
            )

            # Exclusive content - every 3 hours
            self.scheduler.add_job(
                self.orchestrator.exclusive_content_agent.run,
                trigger=IntervalTrigger(hours=3),
                id="exclusive_content",
                name="Exclusive Content",
                replace_existing=True
            )

            # Community moderation - every 30 minutes
            self.scheduler.add_job(
                self.orchestrator.community_moderator.run,
                trigger=IntervalTrigger(minutes=30),
                id="moderation",
                name="Community Moderation",
                replace_existing=True
            )

            # Full Phase 3 pipeline - daily at 6 AM UTC
            self.scheduler.add_job(
                self.orchestrator.run_full_pipeline_phase3,
                trigger=CronTrigger(hour=6, minute=0),
                id="daily_full_pipeline",
                name="Daily Full Pipeline (Phase 3)",
                replace_existing=True
            )

            logger.info("Scheduled jobs configured (Phase 3):")
            logger.info("  - Market Scan: Every 30 minutes")
            logger.info("  - Analysis: Every 2 hours")
            logger.info("  - Content Creation: Every 3 hours")
            logger.info("  - Engagement: Every hour")
            logger.info("  - Analytics: Every 6 hours")
            logger.info("  - Content Repurposing: Daily at 10 AM UTC")
            logger.info("  - Conversion: Every 4 hours")
            logger.info("  - Onboarding: Every 2 hours")
            logger.info("  - Exclusive Content: Every 3 hours")
            logger.info("  - Moderation: Every 30 minutes")
            logger.info("  - Full Phase 3 Pipeline: Daily at 6 AM UTC")

        elif self.phase >= 2:
            # Phase 2 jobs only

            # Engagement - every hour
            self.scheduler.add_job(
                self.orchestrator.run_engagement_pipeline,
                trigger=IntervalTrigger(hours=1),
                id="engagement",
                name="Engagement Pipeline",
                replace_existing=True
            )

            # Analytics collection - every 6 hours
            self.scheduler.add_job(
                self.orchestrator.analytics_agent.run,
                trigger=IntervalTrigger(hours=6),
                id="analytics",
                name="Analytics Collection",
                replace_existing=True
            )

            # Content repurposing - daily at 10 AM UTC
            self.scheduler.add_job(
                self.orchestrator.content_strategist.plan_content_repurposing,
                trigger=CronTrigger(hour=10, minute=0),
                id="content_repurposing",
                name="Content Repurposing",
                replace_existing=True
            )

            # Full Phase 2 pipeline - daily at 6 AM UTC
            self.scheduler.add_job(
                self.orchestrator.run_full_pipeline_phase2,
                trigger=CronTrigger(hour=6, minute=0),
                id="daily_full_pipeline",
                name="Daily Full Pipeline (Phase 2)",
                replace_existing=True
            )

            logger.info("Scheduled jobs configured (Phase 2):")
            logger.info("  - Market Scan: Every 30 minutes")
            logger.info("  - Analysis: Every 2 hours")
            logger.info("  - Content Creation: Every 3 hours")
            logger.info("  - Engagement: Every hour")
            logger.info("  - Analytics: Every 6 hours")
            logger.info("  - Content Repurposing: Daily at 10 AM UTC")
            logger.info("  - Full Phase 2 Pipeline: Daily at 6 AM UTC")

        else:
            # Phase 1 only - Full pipeline daily at 6 AM UTC
            self.scheduler.add_job(
                self.orchestrator.run_full_pipeline,
                trigger=CronTrigger(hour=6, minute=0),
                id="daily_full_pipeline",
                name="Daily Full Pipeline",
                replace_existing=True
            )

            logger.info("Scheduled jobs configured (Phase 1):")
            logger.info("  - Market Scan: Every 30 minutes")
            logger.info("  - Analysis: Every 2 hours")
            logger.info("  - Content Creation: Every 3 hours")
            logger.info("  - Full Pipeline: Daily at 6 AM UTC")

    async def _run_analysis_pipeline(self):
        """Run analysis and content strategy."""
        await self.orchestrator.run_analysis_only()
        await self.orchestrator.content_strategist.run()

    def start(self):
        """Start the scheduler."""
        logger.info("Starting scheduler...")
        self.scheduler.start()
        logger.info("Scheduler started successfully!")

        # Print next run times
        logger.info("\nNext scheduled runs:")
        for job in self.scheduler.get_jobs():
            logger.info(f"  - {job.name}: {job.next_run_time}")

    def stop(self):
        """Stop the scheduler."""
        logger.info("Stopping scheduler...")
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

    async def run_now(self, job_id: str = "full_pipeline"):
        """
        Run a specific job immediately.

        Args:
            job_id: ID of the job to run
        """
        logger.info(f"Running job immediately: {job_id}")

        if job_id == "full_pipeline":
            return await self.orchestrator.run_full_pipeline()
        elif job_id == "market_scan":
            return await self.orchestrator.run_market_scan_only()
        elif job_id == "analysis":
            return await self.orchestrator.run_analysis_only()
        elif job_id == "content_creation":
            return await self.orchestrator.run_content_creation_pipeline()
        else:
            logger.error(f"Unknown job ID: {job_id}")
            return None


async def main():
    """Main entry point for the scheduler."""
    scheduler = ContentCreatorScheduler()

    # Start the scheduler
    scheduler.start()

    # Run the full pipeline once immediately
    logger.info("\nRunning initial full pipeline...")
    await scheduler.orchestrator.run_full_pipeline()

    # Keep the scheduler running
    try:
        logger.info("\nScheduler is running. Press Ctrl+C to exit.")
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("\nShutting down...")
        scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())
