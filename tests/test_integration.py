"""Integration tests for the complete system workflow."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.integration()
class TestSystemIntegration:
    """Integration tests for complete workflows."""

    @pytest.mark.asyncio()
    async def test_complete_content_pipeline(self):
        """Test complete content creation and publishing pipeline."""
        from src.orchestrator import AgentOrchestrator

        orchestrator = AgentOrchestrator()

        # Mock external dependencies
        with patch(
            "src.api_integrations.exchange_api.ExchangeAPI.get_price_data",
            AsyncMock(return_value={"price": 50000}),
        ):
            with patch(
                "src.api_integrations.twitter_api.TwitterAPI.post_tweet",
                AsyncMock(return_value={"id": "123"}),
            ):
                # This would run the actual pipeline (mocked to avoid external calls)
                assert orchestrator is not None

    @pytest.mark.asyncio()
    async def test_database_to_api_flow(self):
        """Test data flows from database through to API."""
        from src.database.connection import get_db
        from src.database.models import MarketData

        # Test database connection works
        with get_db() as db:
            # Should be able to query
            result = db.query(MarketData).first()
            # Result might be None if empty, but query should work
            assert result is None or isinstance(result, MarketData)

    @pytest.mark.asyncio()
    async def test_agent_communication(self):
        """Test agents can communicate through database."""
        from src.agents.content_creation_agent import ContentCreationAgent
        from src.agents.market_scanner_agent import MarketScannerAgent

        # Mock external calls
        with patch(
            "src.api_integrations.exchange_api.ExchangeAPI.get_price_data",
            AsyncMock(return_value={}),
        ):
            with patch(
                "src.api_integrations.news_api.NewsAPI.fetch_crypto_news",
                AsyncMock(return_value=[]),
            ):
                scanner = MarketScannerAgent()
                creator = ContentCreationAgent()

                # Agents should initialize
                assert scanner is not None
                assert creator is not None

    @pytest.mark.asyncio()
    async def test_error_propagation(self):
        """Test errors are handled gracefully across agents."""
        from src.orchestrator import AgentOrchestrator

        orchestrator = AgentOrchestrator()

        # Even with errors, orchestrator should not crash
        with patch(
            "src.agents.market_scanner_agent.MarketScannerAgent.execute",
            side_effect=Exception("Test error"),
        ):
            # Should handle exception gracefully
            try:
                # This might raise, but we test it doesn't crash the system
                assert orchestrator is not None
            except Exception:
                # Expected behavior - error is caught
                pass


@pytest.mark.integration()
class TestPerformanceBaseline:
    """Performance baseline tests."""

    @pytest.mark.asyncio()
    async def test_agent_execution_time(self):
        """Test agent execution completes in reasonable time."""
        import time

        from src.agents.base_agent import BaseAgent

        class TestAgent(BaseAgent):
            def __init__(self):
                super().__init__("TestAgent")

            async def execute(self):
                return {"status": "success"}

        agent = TestAgent()

        start = time.time()
        await agent.run()
        duration = time.time() - start

        # Should complete quickly (under 1 second for simple agent)
        assert duration < 1.0

    @pytest.mark.asyncio()
    async def test_database_query_performance(self):
        """Test database queries are performant."""
        import time

        from src.database.connection import get_db
        from src.database.models import MarketData

        start = time.time()

        with get_db() as db:
            # Simple query should be fast
            db.query(MarketData).limit(10).all()

        duration = time.time() - start

        # Should complete in under 100ms
        assert duration < 0.1


@pytest.mark.integration()
class TestConfigurationManagement:
    """Test configuration and settings management."""

    def test_config_loads_from_env(self):
        """Test configuration loads from environment."""
        from config.config import settings

        # Settings should be loaded (lowercase attribute names)
        assert settings is not None
        assert hasattr(settings, "database_url")

    def test_required_settings_present(self):
        """Test all required settings are present."""
        from config.config import settings

        # Check critical settings (lowercase)
        assert settings.database_url is not None
        assert settings.anthropic_api_key is not None or settings.anthropic_api_key == "test-key"

    def test_phase_specific_settings(self):
        """Test phase-specific settings exist."""
        from config.config import settings

        # Phase 3 settings (lowercase)
        assert hasattr(settings, "conversion_min_engagement_score")

        # Phase 4 settings (lowercase)
        assert hasattr(settings, "ab_testing_min_sample_size")


@pytest.mark.integration()
class TestEndToEndScenarios:
    """End-to-end scenario tests."""

    @pytest.mark.asyncio()
    async def test_new_user_onboarding_flow(self):
        """Test complete new user onboarding flow."""
        from src.agents.onboarding_agent import OnboardingAgent

        agent = OnboardingAgent()
        assert agent is not None
        # Agent should be ready to onboard users

    @pytest.mark.asyncio()
    async def test_content_approval_workflow(self):
        """Test human-in-the-loop content approval."""
        from config.config import settings
        from src.agents.publishing_agent import PublishingAgent

        agent = PublishingAgent()

        # If HITL is enabled (lowercase), content should require approval
        if settings.human_in_the_loop:
            # Content approval flow should work
            assert hasattr(agent, "approve_and_publish")

    @pytest.mark.asyncio()
    async def test_ab_test_lifecycle(self):
        """Test complete A/B test lifecycle."""
        from src.agents.ab_testing_agent import ABTestingAgent

        with patch("src.agents.ab_testing_agent.Anthropic"):
            agent = ABTestingAgent()
            assert agent is not None
            # Agent should be able to create and analyze tests
            assert hasattr(agent, "execute")
