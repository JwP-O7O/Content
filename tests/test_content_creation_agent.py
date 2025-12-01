import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from src.agents.content_creation_agent import ContentCreationAgent
from src.database.models import Base, Insight, ContentPlan, InsightType, ContentFormat

@pytest.fixture
def mock_settings():
    """Mock application settings."""
    with patch('config.config.settings') as mock_settings:
        mock_settings.content_personality = "hyper-analytical"
        yield mock_settings

@pytest.fixture
def mock_db_session():
    """Fixture for an in-memory SQLite database session."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        # Add a sample content plan to be processed
        insight = Insight(asset="BTC", type=InsightType.BREAKOUT, confidence=0.8, details={"price": 52000})
        db.add(insight)
        db.commit() # Commit to get the insight ID

        plan = ContentPlan(insight_id=insight.id, platform="twitter", format=ContentFormat.SINGLE_TWEET, status="pending")
        db.add(plan)
        db.commit()
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)

@pytest.fixture(autouse=True)
def patch_get_db(mock_db_session):
    """Patch get_db to use the mock session."""
    with patch('src.agents.content_creation_agent.get_db') as mock_get_db:
        mock_get_db.return_value.__enter__.return_value = mock_db_session
        yield

@pytest.fixture
def mock_llm_client():
    """Fixture for a mocked LLM client."""
    with patch('src.agents.content_creation_agent.llm_client', new_callable=MagicMock) as mock_client:
        mock_client.generate.return_value = "Generated test content for a tweet about $BTC."
        yield mock_client


class TestContentCreationAgent:

    @pytest.mark.asyncio
    async def test_initialization(self, mock_settings):
        """Test agent initialization."""
        agent = ContentCreationAgent()
        assert agent.name == "ContentCreationAgent"
        assert agent.personality == "hyper-analytical"

    @pytest.mark.asyncio
    async def test_execute_success(self, mock_llm_client, mock_db_session, mock_settings):
        """Test successful execution of the agent."""
        agent = ContentCreationAgent()
        results = await agent.execute()

        # Check if the LLM client was called
        mock_llm_client.generate.assert_called_once()
        
        # Check the results summary
        assert results["content_created"] == 1
        assert results["tweets"] == 1
        assert not results["errors"]

        # Check if the content plan status was updated in the DB
        plan = mock_db_session.query(ContentPlan).first()
        assert plan.status == "ready"


    @pytest.mark.asyncio
    async def test_no_pending_plans(self, mock_llm_client, mock_db_session, mock_settings):
        """Test execution when there are no pending plans."""
        # Set the existing plan to 'ready'
        plan = mock_db_session.query(ContentPlan).first()
        plan.status = 'ready'
        mock_db_session.commit()
        
        agent = ContentCreationAgent()
        results = await agent.execute()

        # LLM should not be called
        mock_llm_client.generate.assert_not_called()
        
        # Results should show no content created
        assert results["content_created"] == 0
