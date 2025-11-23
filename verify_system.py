"""System verification script - Checks if all components are correctly installed."""

import sys

from loguru import logger

from src.utils.logger import setup_logger


class SystemVerifier:
    """Verifies the Content Creator system is correctly configured."""

    def __init__(self):
        """Initialize the verifier."""
        self.errors = []
        self.warnings = []
        self.successes = []

    def verify_all(self) -> dict:
        """
        Run all verification checks.

        Returns:
            Dictionary with verification results
        """
        logger.info("="*60)
        logger.info("Content Creator - System Verification")
        logger.info("="*60)

        # Phase 1: Basic Configuration
        logger.info("\n[PHASE 1] Checking basic configuration...")
        self._check_python_version()
        self._check_imports()
        self._check_config()
        self._check_database_connection()

        # Phase 2: Agent Verification
        logger.info("\n[PHASE 2] Verifying agents...")
        self._check_agents()

        # Phase 3: API Integrations
        logger.info("\n[PHASE 3] Checking API integrations...")
        self._check_api_integrations()

        # Phase 4: Database Schema
        logger.info("\n[PHASE 4] Verifying database schema...")
        self._check_database_schema()

        # Summary
        self._print_summary()

        return {
            "success": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "checks_passed": len(self.successes)
        }

    def _check_python_version(self):
        """Check Python version."""
        version = sys.version_info
        if version.major >= 3 and version.minor >= 9:
            self._success(f"Python version: {version.major}.{version.minor}.{version.micro}")
        else:
            self._error(f"Python 3.9+ required, found {version.major}.{version.minor}.{version.micro}")

    def _check_imports(self):
        """Check if all required packages are installed."""
        packages = [
            ("sqlalchemy", "SQLAlchemy"),
            ("anthropic", "Anthropic"),
            ("tweepy", "Tweepy"),
            ("apscheduler", "APScheduler"),
            ("loguru", "Loguru"),
            ("pydantic", "Pydantic"),
            ("stripe", "Stripe"),
        ]

        for module_name, display_name in packages:
            try:
                __import__(module_name)
                self._success(f"Package installed: {display_name}")
            except ImportError:
                self._error(f"Missing package: {display_name} (pip install {module_name})")

    def _check_config(self):
        """Check configuration."""
        try:
            from config.config import settings

            # Check critical settings
            if settings.anthropic_api_key:
                self._success("Anthropic API key configured")
            else:
                self._error("Anthropic API key not configured")

            if settings.database_url:
                self._success("Database URL configured")
            else:
                self._error("Database URL not configured")

            # Check optional Phase 3 settings
            if settings.stripe_api_key:
                self._success("Stripe API key configured (Phase 3)")
            else:
                self._warning("Stripe API key not configured (required for Phase 3)")

            if settings.discord_bot_token:
                self._success("Discord bot token configured (Phase 3)")
            else:
                self._warning("Discord bot token not configured (required for Phase 3)")

        except Exception as e:
            self._error(f"Configuration error: {e}")

    def _check_database_connection(self):
        """Check database connection."""
        try:
            from src.database.connection import engine

            # Try to connect
            with engine.connect() as conn:
                self._success("Database connection successful")

        except Exception as e:
            self._error(f"Database connection failed: {e}")

    def _check_agents(self):
        """Check if all agents can be imported."""
        agents = [
            # Phase 1
            ("src.agents.market_scanner_agent", "MarketScannerAgent", "Phase 1"),
            ("src.agents.analysis_agent", "AnalysisAgent", "Phase 1"),
            ("src.agents.content_strategist_agent", "ContentStrategistAgent", "Phase 1"),
            ("src.agents.content_creation_agent", "ContentCreationAgent", "Phase 1"),
            ("src.agents.publishing_agent", "PublishingAgent", "Phase 1"),
            # Phase 2
            ("src.agents.engagement_agent", "EngagementAgent", "Phase 2"),
            ("src.agents.image_generation_agent", "ImageGenerationAgent", "Phase 2"),
            ("src.agents.analytics_agent", "AnalyticsAgent", "Phase 2"),
            # Phase 3
            ("src.agents.conversion_agent", "ConversionAgent", "Phase 3"),
            ("src.agents.onboarding_agent", "OnboardingAgent", "Phase 3"),
            ("src.agents.exclusive_content_agent", "ExclusiveContentAgent", "Phase 3"),
            ("src.agents.community_moderator_agent", "CommunityModeratorAgent", "Phase 3"),
            # Phase 4
            ("src.agents.strategy_tuning_agent", "StrategyTuningAgent", "Phase 4"),
            ("src.agents.ab_testing_agent", "ABTestingAgent", "Phase 4"),
            ("src.agents.performance_analytics_agent", "PerformanceAnalyticsAgent", "Phase 4"),
            ("src.agents.feedback_loop_coordinator", "FeedbackLoopCoordinator", "Phase 4"),
        ]

        for module_name, class_name, phase in agents:
            try:
                module = __import__(module_name, fromlist=[class_name])
                getattr(module, class_name)
                self._success(f"Agent available: {class_name} ({phase})")
            except Exception as e:
                self._error(f"Agent import failed: {class_name} - {e}")

    def _check_api_integrations(self):
        """Check API integration modules."""
        apis = [
            ("src.api_integrations.exchange_api", "ExchangeAPI", "Phase 1"),
            ("src.api_integrations.news_api", "NewsAPI", "Phase 1"),
            ("src.api_integrations.twitter_api", "TwitterAPI", "Phase 1"),
            ("src.api_integrations.telegram_api", "TelegramAPI", "Phase 1"),
            ("src.api_integrations.discord_api", "DiscordAPI", "Phase 3"),
            ("src.api_integrations.stripe_api", "StripeAPI", "Phase 3"),
        ]

        for module_name, class_name, phase in apis:
            try:
                module = __import__(module_name, fromlist=[class_name])
                getattr(module, class_name)
                self._success(f"API integration available: {class_name} ({phase})")
            except Exception as e:
                if phase == "Phase 3":
                    self._warning(f"API integration not available: {class_name} - {e}")
                else:
                    self._error(f"API integration import failed: {class_name} - {e}")

    def _check_database_schema(self):
        """Check if database tables exist."""
        try:
            from sqlalchemy import inspect

            from src.database.connection import engine

            inspector = inspect(engine)
            tables = inspector.get_table_names()

            expected_tables = {
                # Phase 1-2
                "market_data": "Phase 1",
                "news_articles": "Phase 1",
                "sentiment_data": "Phase 1",
                "insights": "Phase 1",
                "content_plans": "Phase 1",
                "published_content": "Phase 1",
                "agent_logs": "Phase 1",
                # Phase 3
                "community_users": "Phase 3",
                "subscriptions": "Phase 3",
                "user_interactions": "Phase 3",
                "conversion_attempts": "Phase 3",
                "exclusive_content": "Phase 3",
                "moderation_actions": "Phase 3",
                # Phase 4
                "ab_tests": "Phase 4",
                "ab_test_variants": "Phase 4",
                "performance_snapshots": "Phase 4",
            }

            for table, phase in expected_tables.items():
                if table in tables:
                    self._success(f"Table exists: {table} ({phase})")
                else:
                    self._warning(f"Table missing: {table} ({phase}) - Run 'python init_db.py'")

        except Exception as e:
            self._error(f"Database schema check failed: {e}")

    def _check_orchestrator(self):
        """Check orchestrator."""
        try:
            from src.orchestrator import AgentOrchestrator

            orchestrator = AgentOrchestrator()
            self._success("Orchestrator initialized successfully")

            # Check all agents are initialized
            required_agents = [
                "market_scanner", "analysis_agent", "content_strategist",
                "content_creator", "publisher", "engagement_agent",
                "image_generator", "analytics_agent", "conversion_agent",
                "onboarding_agent", "exclusive_content_agent",
                "community_moderator", "strategy_tuning", "ab_testing",
                "performance_analytics", "feedback_loop"
            ]

            for agent_name in required_agents:
                if hasattr(orchestrator, agent_name):
                    self._success(f"Orchestrator agent ready: {agent_name}")
                else:
                    self._error(f"Orchestrator missing agent: {agent_name}")

        except Exception as e:
            self._error(f"Orchestrator check failed: {e}")

    def _success(self, message: str):
        """Log a success."""
        logger.info(f"✓ {message}")
        self.successes.append(message)

    def _warning(self, message: str):
        """Log a warning."""
        logger.warning(f"⚠ {message}")
        self.warnings.append(message)

    def _error(self, message: str):
        """Log an error."""
        logger.error(f"✗ {message}")
        self.errors.append(message)

    def _print_summary(self):
        """Print verification summary."""
        logger.info("\n" + "="*60)
        logger.info("VERIFICATION SUMMARY")
        logger.info("="*60)

        logger.info(f"\n✓ Passed: {len(self.successes)}")
        logger.info(f"⚠ Warnings: {len(self.warnings)}")
        logger.info(f"✗ Errors: {len(self.errors)}")

        if self.errors:
            logger.error("\nCritical errors found:")
            for error in self.errors:
                logger.error(f"  - {error}")

        if self.warnings:
            logger.warning("\nWarnings (optional features):")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")

        logger.info("\n" + "="*60)

        if not self.errors:
            logger.success("✓ System verification PASSED! Ready to run.")
        else:
            logger.error("✗ System verification FAILED. Fix errors above.")


def main():
    """Main entry point."""
    setup_logger()

    verifier = SystemVerifier()
    results = verifier.verify_all()

    if results["success"]:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
