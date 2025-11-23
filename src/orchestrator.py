"""Main orchestrator that coordinates all agents."""

import asyncio
from datetime import datetime
from loguru import logger

from src.agents.market_scanner_agent import MarketScannerAgent

# Optional import - AnalysisAgent requires pandas which may not be available on Termux
try:
    from src.agents.analysis_agent import AnalysisAgent
    ANALYSIS_AGENT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"AnalysisAgent not available: {e}")
    AnalysisAgent = None
    ANALYSIS_AGENT_AVAILABLE = False

from src.agents.content_strategist_agent import ContentStrategistAgent
from src.agents.content_creation_agent import ContentCreationAgent
from src.agents.publishing_agent import PublishingAgent
from src.agents.engagement_agent import EngagementAgent
from src.agents.image_generation_agent import ImageGenerationAgent
from src.agents.analytics_agent import AnalyticsAgent
from src.agents.conversion_agent import ConversionAgent
from src.agents.onboarding_agent import OnboardingAgent
from src.agents.exclusive_content_agent import ExclusiveContentAgent
from src.agents.community_moderator_agent import CommunityModeratorAgent
from src.agents.strategy_tuning_agent import StrategyTuningAgent
from src.agents.ab_testing_agent import ABTestingAgent
from src.agents.performance_analytics_agent import PerformanceAnalyticsAgent
from src.agents.feedback_loop_coordinator import FeedbackLoopCoordinator


class AgentOrchestrator:
    """
    Orchestrates the entire agent workflow.

    This is the "master agent" that coordinates all other agents.
    """

    def __init__(self):
        """Initialize the orchestrator and all agents."""
        logger.info("Initializing Agent Orchestrator...")

        # Phase 1 agents
        self.market_scanner = MarketScannerAgent()

        # AnalysisAgent is optional (requires pandas)
        if ANALYSIS_AGENT_AVAILABLE:
            self.analysis_agent = AnalysisAgent()
        else:
            self.analysis_agent = None
            logger.warning("AnalysisAgent not initialized (pandas not available)")

        self.content_strategist = ContentStrategistAgent()
        self.content_creator = ContentCreationAgent()
        self.publisher = PublishingAgent()

        # Phase 2 agents
        self.engagement_agent = EngagementAgent()
        self.image_generator = ImageGenerationAgent()
        self.analytics_agent = AnalyticsAgent()

        # Phase 3 agents
        self.conversion_agent = ConversionAgent()
        self.onboarding_agent = OnboardingAgent()
        self.exclusive_content_agent = ExclusiveContentAgent()
        self.community_moderator = CommunityModeratorAgent()

        # Phase 4 agents - Optimization & Self-Learning
        self.strategy_tuning = StrategyTuningAgent()
        self.ab_testing = ABTestingAgent()
        self.performance_analytics = PerformanceAnalyticsAgent()
        self.feedback_loop = FeedbackLoopCoordinator()

        logger.info("All agents initialized successfully (Phase 1-4)")

    async def run_full_pipeline(self) -> dict:
        """
        Run the complete agent pipeline from scanning to publishing.

        Returns:
            Dictionary with results from each agent
        """
        logger.info("="*50)
        logger.info("Starting Full Agent Pipeline")
        logger.info("="*50)

        pipeline_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "agents": {}
        }

        try:
            # Step 1: Market Scanner
            logger.info("Step 1/5: Running Market Scanner...")
            scan_results = await self.market_scanner.run()
            pipeline_results["agents"]["market_scanner"] = scan_results

            # Step 2: Analysis Agent (optional)
            if self.analysis_agent:
                logger.info("Step 2/5: Running Analysis Agent...")
                analysis_results = await self.analysis_agent.run()
                pipeline_results["agents"]["analysis"] = analysis_results
            else:
                logger.warning("Step 2/5: Skipping Analysis Agent (not available)")
                pipeline_results["agents"]["analysis"] = {"status": "skipped", "reason": "pandas not available"}

            # Step 3: Content Strategist
            logger.info("Step 3/5: Running Content Strategist...")
            strategy_results = await self.content_strategist.run()
            pipeline_results["agents"]["content_strategist"] = strategy_results

            # Step 4: Content Creator
            logger.info("Step 4/5: Running Content Creator...")
            creation_results = await self.content_creator.run()
            pipeline_results["agents"]["content_creator"] = creation_results

            # Step 5: Publisher
            logger.info("Step 5/5: Running Publisher...")
            publishing_results = await self.publisher.run()
            pipeline_results["agents"]["publisher"] = publishing_results

            logger.info("="*50)
            logger.info("Pipeline Complete!")
            logger.info("="*50)
            logger.info(f"Market Data: {scan_results.get('market_data_collected', 0)} points")
            if self.analysis_agent:
                logger.info(f"Insights: {analysis_results.get('insights_generated', 0)} generated")
            logger.info(f"Content Plans: {strategy_results.get('content_plans_created', 0)} created")
            logger.info(f"Content Created: {creation_results.get('content_created', 0)} pieces")
            logger.info(f"Content Published: {publishing_results.get('content_published', 0)} pieces")

            pipeline_results["status"] = "success"

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            pipeline_results["status"] = "error"
            pipeline_results["error"] = str(e)

        return pipeline_results

    async def run_market_scan_only(self) -> dict:
        """Run only the market scanning step."""
        logger.info("Running market scan only...")
        return await self.market_scanner.run()

    async def run_analysis_only(self) -> dict:
        """Run only the analysis step."""
        if not self.analysis_agent:
            logger.error("AnalysisAgent not available (pandas not installed)")
            return {"status": "error", "message": "AnalysisAgent requires pandas which is not available"}
        logger.info("Running analysis only...")
        return await self.analysis_agent.run()

    async def run_content_creation_pipeline(self) -> dict:
        """Run content strategy, creation, and publishing."""
        logger.info("Running content creation pipeline...")

        results = {}

        # Content strategy
        results["strategy"] = await self.content_strategist.run()

        # Content creation
        results["creation"] = await self.content_creator.run()

        # Publishing
        results["publishing"] = await self.publisher.run()

        return results

    async def get_pending_approvals(self):
        """Get content awaiting approval."""
        return await self.publisher.get_pending_approvals()

    async def approve_content(self, plan_id: int):
        """Approve and publish content."""
        return await self.publisher.approve_and_publish(plan_id)

    async def reject_content(self, plan_id: int):
        """Reject content."""
        return await self.publisher.reject_content(plan_id)

    async def run_engagement_pipeline(self) -> dict:
        """
        Run the engagement pipeline (Phase 2).

        This monitors and engages with the audience.
        """
        logger.info("Running engagement pipeline...")

        results = {}

        # Engage with audience
        results["engagement"] = await self.engagement_agent.run()

        # Collect metrics
        results["analytics"] = await self.analytics_agent.run()

        # Plan content repurposing based on performance
        results["repurposing"] = (
            await self.content_strategist.plan_content_repurposing()
        )

        return results

    async def run_full_pipeline_phase2(self) -> dict:
        """
        Run the complete Phase 2 pipeline with all agents.

        Returns:
            Dictionary with results from all agents
        """
        logger.info("="*50)
        logger.info("Starting Full Pipeline (Phase 2)")
        logger.info("="*50)

        pipeline_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "agents": {}
        }

        try:
            # Step 1: Market Scanner
            logger.info("Step 1/9: Running Market Scanner...")
            scan_results = await self.market_scanner.run()
            pipeline_results["agents"]["market_scanner"] = scan_results

            # Step 2: Analysis Agent (optional)
            if self.analysis_agent:
                logger.info("Step 2/9: Running Analysis Agent...")
                analysis_results = await self.analysis_agent.run()
                pipeline_results["agents"]["analysis"] = analysis_results
            else:
                logger.warning("Step 2/9: Skipping Analysis Agent (not available)")
                pipeline_results["agents"]["analysis"] = {"status": "skipped", "reason": "pandas not available"}

            # Step 3: Image Generation
            logger.info("Step 3/9: Running Image Generator...")
            image_results = await self.image_generator.run()
            pipeline_results["agents"]["image_generator"] = image_results

            # Step 4: Content Strategist
            logger.info("Step 4/9: Running Content Strategist...")
            strategy_results = await self.content_strategist.run()
            pipeline_results["agents"]["content_strategist"] = strategy_results

            # Step 5: Content Creator
            logger.info("Step 5/9: Running Content Creator...")
            creation_results = await self.content_creator.run()
            pipeline_results["agents"]["content_creator"] = creation_results

            # Step 6: Publisher
            logger.info("Step 6/9: Running Publisher...")
            publishing_results = await self.publisher.run()
            pipeline_results["agents"]["publisher"] = publishing_results

            # Step 7: Engagement Agent
            logger.info("Step 7/9: Running Engagement Agent...")
            engagement_results = await self.engagement_agent.run()
            pipeline_results["agents"]["engagement"] = engagement_results

            # Step 8: Analytics
            logger.info("Step 8/9: Running Analytics Agent...")
            analytics_results = await self.analytics_agent.run()
            pipeline_results["agents"]["analytics"] = analytics_results

            # Step 9: Content Repurposing
            logger.info("Step 9/9: Planning Content Repurposing...")
            repurpose_results = (
                await self.content_strategist.plan_content_repurposing()
            )
            pipeline_results["agents"]["repurposing"] = repurpose_results

            logger.info("="*50)
            logger.info("Phase 2 Pipeline Complete!")
            logger.info("="*50)
            logger.info(f"Market Data: {scan_results.get('market_data_collected', 0)} points")
            logger.info(f"Insights: {analysis_results.get('insights_generated', 0)} generated")
            logger.info(f"Images: {image_results.get('images_generated', 0)} created")
            logger.info(f"Content Plans: {strategy_results.get('content_plans_created', 0)} created")
            logger.info(f"Content Created: {creation_results.get('content_created', 0)} pieces")
            logger.info(f"Content Published: {publishing_results.get('content_published', 0)} pieces")
            logger.info(f"Engagement Actions: {engagement_results.get('replies_sent', 0)} replies, {engagement_results.get('likes_given', 0)} likes")
            logger.info(f"Repurpose Plans: {repurpose_results.get('repurpose_plans_created', 0)} created")

            pipeline_results["status"] = "success"

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            pipeline_results["status"] = "error"
            pipeline_results["error"] = str(e)

        return pipeline_results

    async def run_full_pipeline_phase3(self) -> dict:
        """
        Run the complete Phase 3 pipeline with all agents including monetization.

        Returns:
            Dictionary with results from all agents
        """
        logger.info("="*50)
        logger.info("Starting Full Pipeline (Phase 3)")
        logger.info("="*50)

        pipeline_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "agents": {}
        }

        try:
            # Step 1-9: Phase 2 pipeline
            phase2_results = await self.run_full_pipeline_phase2()
            pipeline_results["agents"].update(phase2_results["agents"])

            # Step 10: Conversion Agent
            logger.info("Step 10/12: Running Conversion Agent...")
            conversion_results = await self.conversion_agent.run()
            pipeline_results["agents"]["conversion"] = conversion_results

            # Step 11: Onboarding Agent
            logger.info("Step 11/12: Running Onboarding Agent...")
            onboarding_results = await self.onboarding_agent.run()
            pipeline_results["agents"]["onboarding"] = onboarding_results

            # Step 12: Exclusive Content Agent
            logger.info("Step 12/12: Running Exclusive Content Agent...")
            exclusive_results = await self.exclusive_content_agent.run()
            pipeline_results["agents"]["exclusive_content"] = exclusive_results

            # Step 13: Community Moderator
            logger.info("Step 13/12: Running Community Moderator...")
            moderation_results = await self.community_moderator.run()
            pipeline_results["agents"]["moderation"] = moderation_results

            logger.info("="*50)
            logger.info("Phase 3 Pipeline Complete!")
            logger.info("="*50)
            logger.info(f"Conversions: {conversion_results.get('dms_sent', 0)} DMs sent")
            logger.info(f"Onboarding: {onboarding_results.get('members_onboarded', 0)} members onboarded")
            logger.info(f"Exclusive Content: {exclusive_results.get('content_published', 0)} pieces published")
            logger.info(f"Moderation: {moderation_results.get('violations_detected', 0)} violations detected")

            pipeline_results["status"] = "success"

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            pipeline_results["status"] = "error"
            pipeline_results["error"] = str(e)

        return pipeline_results

    async def run_monetization_pipeline(self) -> dict:
        """
        Run the monetization pipeline (Phase 3 specific).

        Returns:
            Dictionary with monetization results
        """
        logger.info("Running monetization pipeline...")

        results = {}

        # Conversion
        results["conversion"] = await self.conversion_agent.run()

        # Onboarding new members
        results["onboarding"] = await self.onboarding_agent.run()

        # Exclusive content for paying members
        results["exclusive_content"] = await self.exclusive_content_agent.run()

        # Community moderation
        results["moderation"] = await self.community_moderator.run()

        return results

    async def generate_analytics_report(self, days: int = 7) -> str:
        """Generate comprehensive analytics report."""
        return await self.analytics_agent.generate_report(days=days)

    async def get_kpi_dashboard(self) -> dict:
        """Get KPI dashboard data."""
        return await self.analytics_agent.get_kpi_dashboard()

    async def run_full_pipeline_phase4(self) -> dict:
        """
        Run the complete Phase 4 pipeline with all optimization agents.

        Returns:
            Dictionary with results from all agents
        """
        logger.info("="*50)
        logger.info("Starting Full Pipeline (Phase 4)")
        logger.info("="*50)

        pipeline_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "agents": {}
        }

        try:
            # Step 1-13: Phase 3 pipeline
            phase3_results = await self.run_full_pipeline_phase3()
            pipeline_results["agents"].update(phase3_results["agents"])

            # Step 14: Performance Analytics
            logger.info("Step 14/16: Running Performance Analytics...")
            analytics_results = await self.performance_analytics.run()
            pipeline_results["agents"]["performance_analytics"] = analytics_results

            # Step 15: A/B Testing
            logger.info("Step 15/16: Running A/B Testing...")
            ab_results = await self.ab_testing.run()
            pipeline_results["agents"]["ab_testing"] = ab_results

            # Step 16: Feedback Loop Coordination
            logger.info("Step 16/16: Running Feedback Loop Coordination...")
            feedback_results = await self.feedback_loop.run()
            pipeline_results["agents"]["feedback_loop"] = feedback_results

            logger.info("="*50)
            logger.info("Phase 4 Pipeline Complete!")
            logger.info("="*50)
            logger.info(f"Performance Snapshots: {analytics_results.get('snapshots_created', 0)}")
            logger.info(f"A/B Tests: {ab_results.get('new_tests_created', 0)} created, {ab_results.get('tests_completed', 0)} completed")
            logger.info(f"Optimization Cycle: {'Complete' if feedback_results.get('cycle_complete') else 'Incomplete'}")

            pipeline_results["status"] = "success"

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            pipeline_results["status"] = "error"
            pipeline_results["error"] = str(e)

        return pipeline_results

    async def run_optimization_pipeline(self) -> dict:
        """
        Run the optimization pipeline (Phase 4 specific).

        Returns:
            Dictionary with optimization results
        """
        logger.info("Running optimization pipeline...")

        results = {}

        # Performance analytics
        results["performance_analytics"] = await self.performance_analytics.run()

        # A/B testing
        results["ab_testing"] = await self.ab_testing.run()

        # Strategy tuning
        results["strategy_tuning"] = await self.strategy_tuning.run()

        # Feedback loop coordination
        results["feedback_loop"] = await self.feedback_loop.run()

        return results

    async def get_system_health(self) -> dict:
        """Get overall system health metrics."""
        return await self.feedback_loop.get_system_health_score()

    async def generate_learning_report(self, days: int = 7) -> str:
        """Generate comprehensive learning report."""
        return await self.feedback_loop.generate_learning_report(days=days)


async def main():
    """Main entry point for running the orchestrator."""
    orchestrator = AgentOrchestrator()

    # Run the full pipeline
    results = await orchestrator.run_full_pipeline()

    return results


if __name__ == "__main__":
    asyncio.run(main())
