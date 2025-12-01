import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

# Conditional for skipping tests if pandas is not available
try:
    import pandas as pd
    pandas_not_installed = False
except ImportError:
    pandas_not_installed = True

# We still need these for type hinting if pandas is available
if not pandas_not_installed:
    from src.agents.analysis_agent import AnalysisAgent, Insight, InsightType
    from src.database.models import Base, MarketData, NewsArticle, SentimentData

skip_if_no_pandas = pytest.mark.skipif(pandas_not_installed, reason="pandas is not installed")

@pytest.fixture(autouse=True)
def mock_settings():
    """Mock application settings."""
    with patch('config.config.settings') as mock_settings:
        mock_settings.anthropic_api_key = "mock_key"
        yield mock_settings

@pytest.fixture
def mock_db_session():
    """Fixture for an in-memory SQLite database session."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.database.models import Base # This is safe to import

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        # Pre-populate with some data only if pandas is available
        if not pandas_not_installed:
            db.add(MarketData(asset="BTC", price=50000, volume_24h=1000, timestamp=datetime.utcnow()))
            db.add(NewsArticle(title="Big news for BTC", url="http://test.com/1", summary="Positive summary for BTC", published_at=datetime.utcnow()))
            db.add(SentimentData(asset="BTC", volume=100, timestamp=datetime.utcnow()))
            db.commit()
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)

@pytest.fixture(autouse=True)
def patch_get_db(mock_db_session):
    """Patch get_db to use the mock session."""
    if not pandas_not_installed:
        with patch('src.agents.analysis_agent.get_db') as mock_get_db:
            mock_get_db.return_value.__enter__.return_value = mock_db_session
            yield
    else:
        yield

@skip_if_no_pandas
class TestAnalysisAgent:

    @pytest.fixture
    def agent(self):
        """Fixture for an AnalysisAgent instance."""
        with patch('src.agents.analysis_agent.Anthropic', new_callable=MagicMock) as MockAnthropic:
            MockAnthropic.return_value.messages.create = AsyncMock(return_value=MagicMock(content=[MagicMock(text="LLM analysis text")]))
            agent = AnalysisAgent()
            agent.llm_client = MockAnthropic.return_value
            return agent

    @pytest.mark.asyncio
    async def test_initialization(self, agent):
        """Test agent initialization."""
        assert agent.name == "AnalysisAgent"
        assert agent.llm_client is not None

    @pytest.mark.asyncio
    async def test_get_active_assets(self, agent, mock_db_session):
        """Test fetching active assets from the database."""
        assets = await agent._get_active_assets()
        assert "BTC" in assets

    @pytest.mark.asyncio
    async def test_technical_analysis_breakout(self, agent):
        """Test technical analysis for a breakout scenario."""
        # Create a sample DataFrame for a breakout
        timestamps = [datetime.utcnow() - timedelta(minutes=i) for i in range(20)]
        market_data = pd.DataFrame({
            "timestamp": timestamps[::-1],
            "price": [50000 + i*100 for i in range(20)],
            "volume": [1000 + i*50 for i in range(20)],
            "change": [0.1 + i*0.2 for i in range(20)]
        })
        market_data.iloc[-1, market_data.columns.get_loc('change')] = 6.0 # breakout change
        market_data.iloc[-1, market_data.columns.get_loc('volume')] = 3000 # high volume

        insights = await agent._technical_analysis("BTC", market_data)

        assert len(insights) == 1
        insight = insights[0]
        assert insight.type == InsightType.BREAKOUT
        assert insight.asset == "BTC"
        assert insight.confidence > 0.6
        assert "llm_analysis" in insight.details

    @pytest.mark.asyncio
    async def test_news_impact_analysis(self, agent):
        """Test news impact analysis."""
        news_articles = [
            NewsArticle(title="News 1", summary="Positive for BTC"),
            NewsArticle(title="News 2", summary="Also good for BTC"),
            NewsArticle(title="News 3", summary="Everyone loves BTC"),
        ]
        
        insights = await agent._news_impact_analysis("BTC", news_articles)

        assert len(insights) == 1
        insight = insights[0]
        assert insight.type == InsightType.NEWS_IMPACT
        assert insight.asset == "BTC"
        assert insight.details["news_count"] == 3
        assert "llm_analysis" in insight.details

    @pytest.mark.asyncio
    async def test_execute_pipeline(self, agent, mock_db_session):
        """Test the full execute pipeline of the agent."""
        results = await agent.execute()

        assert results["insights_generated"] > 0
        assert results["assets_analyzed"] == 1
        
        # Check if insights were actually added to the DB
        insight_count = mock_db_session.query(Insight).count()
        assert insight_count > 0