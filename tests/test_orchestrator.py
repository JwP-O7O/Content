import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.orchestrator import AgentOrchestrator
from src.agents.base_agent import BaseAgent # Using BaseAgent for generic spec

# Mock the settings to prevent real API calls during testing
@pytest.fixture(autouse=True)
def mock_settings():
    with patch('config.config.settings') as mock_settings:
        mock_settings.database_url = "sqlite:///./test.db"
        mock_settings.anthropic_api_key = "mock_key"
        mock_settings.google_api_key = "mock_key"
        mock_settings.twitter_api_key = "mock_key"
        mock_settings.twitter_api_secret = "mock_key"
        mock_settings.twitter_access_token = "mock_key"
        mock_settings.twitter_access_token_secret = "mock_key"
        mock_settings.twitter_bearer_token = "mock_key"
        mock_settings.telegram_bot_token = "mock_key"
        mock_settings.telegram_channel_id = "mock_channel"
        mock_settings.human_in_the_loop = False
        mock_settings.content_personality = "hyper-analytical"
        mock_settings.db_user = "testuser"
        mock_settings.db_password = "testpass"
        mock_settings.db_name = "testdb"
        # Add other necessary settings mocks here
        yield mock_settings

# Mock the get_db function to use an in-memory SQLite database for testing
@pytest.fixture(name="db_session")
def mock_db_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.database.models import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)

# Patch get_db to return our mock session
@pytest.fixture(autouse=True)
def patch_get_db(db_session):
    with patch('src.database.connection.get_db') as mock_get_db:
        mock_get_db.return_value.__enter__.return_value = db_session
        yield


class TestAgentOrchestrator:
    
    @pytest.fixture
    def mock_agents(self):
        """A fixture to mock all agent classes and their instances."""
        with patch('src.orchestrator.MarketScannerAgent', new_callable=MagicMock) as MockMarketScannerAgent, \
             patch('src.orchestrator.AnalysisAgent', new_callable=MagicMock) as MockAnalysisAgent, \
             patch('src.orchestrator.ContentStrategistAgent', new_callable=MagicMock) as MockContentStrategistAgent, \
             patch('src.orchestrator.ContentCreationAgent', new_callable=MagicMock) as MockContentCreationAgent, \
             patch('src.orchestrator.PublishingAgent', new_callable=MagicMock) as MockPublishingAgent, \
             patch('src.orchestrator.EngagementAgent', new_callable=MagicMock) as MockEngagementAgent, \
             patch('src.orchestrator.ImageGenerationAgent', new_callable=MagicMock) as MockImageGenerationAgent, \
             patch('src.orchestrator.AnalyticsAgent', new_callable=MagicMock) as MockAnalyticsAgent, \
             patch('src.orchestrator.ConversionAgent', new_callable=MagicMock) as MockConversionAgent, \
             patch('src.orchestrator.OnboardingAgent', new_callable=MagicMock) as MockOnboardingAgent, \
             patch('src.orchestrator.ExclusiveContentAgent', new_callable=MagicMock) as MockExclusiveContentAgent, \
             patch('src.orchestrator.CommunityModeratorAgent', new_callable=MagicMock) as MockCommunityModeratorAgent, \
             patch('src.orchestrator.StrategyTuningAgent', new_callable=MagicMock) as MockStrategyTuningAgent, \
             patch('src.orchestrator.ABTestingAgent', new_callable=MagicMock) as MockABTestingAgent, \
             patch('src.orchestrator.PerformanceAnalyticsAgent', new_callable=MagicMock) as MockPerformanceAnalyticsAgent, \
             patch('src.orchestrator.FeedbackLoopCoordinator', new_callable=MagicMock) as MockFeedbackLoopCoordinator, \
             patch('src.orchestrator.ANALYSIS_AGENT_AVAILABLE', True):

            # Configure the return_value of each class to be an AsyncMock instance
            mocks = {
                "MarketScannerAgent": MockMarketScannerAgent,
                "AnalysisAgent": MockAnalysisAgent,
                "ContentStrategistAgent": MockContentStrategistAgent,
                "ContentCreationAgent": MockContentCreationAgent,
                "PublishingAgent": MockPublishingAgent,
            }
            
            for name, mock_class in mocks.items():
                mock_instance = AsyncMock(spec=BaseAgent)
                mock_class.return_value = mock_instance

            yield mocks


    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, mock_settings, mock_agents):
        """Test that the orchestrator initializes all agents."""
        orchestrator = AgentOrchestrator()
        
        # Verify that the mocked classes were called to create instances
        for agent_name, mock_class in mock_agents.items():
            mock_class.assert_called_once()
        
        assert isinstance(orchestrator.market_scanner, AsyncMock)
        assert isinstance(orchestrator.analysis_agent, AsyncMock)
        assert isinstance(orchestrator.content_strategist, AsyncMock)

    @pytest.mark.asyncio
    async def test_run_full_pipeline_success(self, mock_settings, db_session, mock_agents):
        """Test successful execution of the full pipeline."""
        
        # Configure mocks for successful runs
        mock_agents["MarketScannerAgent"].return_value.run.return_value = {"market_data_collected": 10}
        mock_agents["AnalysisAgent"].return_value.run.return_value = {"insights_generated": 5}
        mock_agents["ContentStrategistAgent"].return_value.run.return_value = {"content_plans_created": 3}
        mock_agents["ContentCreationAgent"].return_value.run.return_value = {"content_created": 3}
        mock_agents["PublishingAgent"].return_value.run.return_value = {"content_published": 3}

        orchestrator = AgentOrchestrator()
        results = await orchestrator.run_full_pipeline()

        # Assertions to ensure each agent's run method was called
        mock_agents["MarketScannerAgent"].return_value.run.assert_awaited_once()
        mock_agents["AnalysisAgent"].return_value.run.assert_awaited_once()
        mock_agents["ContentStrategistAgent"].return_value.run.assert_awaited_once()
        mock_agents["ContentCreationAgent"].return_value.run.assert_awaited_once()
        mock_agents["PublishingAgent"].return_value.run.assert_awaited_once()

        assert results["status"] == "success"
        assert results["agents"]["market_scanner"] == {"market_data_collected": 10}
        assert results["agents"]["analysis"] == {"insights_generated": 5}
        assert results["agents"]["content_strategist"] == {"content_plans_created": 3}
        assert results["agents"]["content_creator"] == {"content_created": 3}
        assert results["agents"]["publisher"] == {"content_published": 3}

    @pytest.mark.asyncio
    async def test_run_full_pipeline_error_handling(self, mock_settings, db_session, mock_agents):
        """Test error handling in the full pipeline."""

        # Configure one agent to raise an exception
        mock_agents["MarketScannerAgent"].return_value.run.side_effect = Exception("Market scan failed")

        orchestrator = AgentOrchestrator()
        results = await orchestrator.run_full_pipeline()

        # Assert that the pipeline reported an error
        assert results["status"] == "error"
        assert "Market scan failed" in results["error"]

        # Ensure that the failing agent was called
        mock_agents["MarketScannerAgent"].return_value.run.assert_awaited_once()
        # Subsequent agents should not be called
        mock_agents["AnalysisAgent"].return_value.run.assert_not_called()
        mock_agents["ContentStrategistAgent"].return_value.run.assert_not_called()
        mock_agents["ContentCreationAgent"].return_value.run.assert_not_called()
        mock_agents["PublishingAgent"].return_value.run.assert_not_called()