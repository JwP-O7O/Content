import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime # Import datetime
from src.agents.market_scanner_agent import MarketScannerAgent
from src.database.connection import get_db
from src.database.models import Base

@pytest.fixture(autouse=True)
def mock_settings():
    with patch('config.config.settings') as mock_settings:
        mock_settings.binance_api_key = "mock_key"
        mock_settings.binance_api_secret = "mock_secret"
        mock_settings.twitter_api_key = "mock_key"
        mock_settings.twitter_api_secret = "mock_secret"
        mock_settings.twitter_access_token = "mock_token"
        mock_settings.twitter_access_token_secret = "mock_token_secret"
        mock_settings.twitter_bearer_token = "mock_bearer"
        yield mock_settings

@pytest.fixture
def mock_db_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)

@pytest.fixture(autouse=True)
def patch_get_db(mock_db_session):
    # Patch the get_db function specifically where it's used in the agent
    with patch('src.agents.market_scanner_agent.get_db') as mock_get_db:
        mock_get_db.return_value.__enter__.return_value = mock_db_session
        yield

@pytest.fixture
def mock_api_clients():
    with patch('src.agents.market_scanner_agent.ExchangeAPI', new_callable=MagicMock) as MockExchangeAPI, \
         patch('src.agents.market_scanner_agent.NewsAPI', new_callable=MagicMock) as MockNewsAPI, \
         patch('src.agents.market_scanner_agent.TwitterAPI', new_callable=MagicMock) as MockTwitterAPI:
        
        mock_exchange_api = MockExchangeAPI.return_value
        mock_exchange_api.get_ticker_24h = AsyncMock(return_value={
            "price": "50000", "volume_24h": "1000", "price_change_24h": "1.5", "raw_data": {}
        })
        mock_exchange_api.get_top_gainers_losers = AsyncMock(return_value={
            "gainers": [{"symbol": "GNR", "change_percent": 10.0}],
            "losers": [{"symbol": "LSR", "change_percent": -10.0}]
        })

        mock_news_api = MockNewsAPI.return_value
        mock_news_api.fetch_latest_news = AsyncMock(return_value=[
            {"title": "Test News", "url": "http://test.com/news", "source": "Test Source", "published_at": datetime(2025, 1, 1), "content": "Test content", "summary": "Test summary"}
        ])

        mock_twitter_api = MockTwitterAPI.return_value
        mock_twitter_api.get_sentiment_for_asset = MagicMock(return_value={
            "volume": 100, "raw_data": {}
        })

        yield {
            "exchange": mock_exchange_api,
            "news": mock_news_api,
            "twitter": mock_twitter_api
        }


class TestMarketScannerAgent:
    @pytest.mark.asyncio
    async def test_initialization(self, mock_api_clients):
        """Test the initialization of the MarketScannerAgent."""
        agent = MarketScannerAgent()
        assert agent.name == "MarketScannerAgent"
        assert agent.exchange_api is not None
        assert agent.news_api is not None
        assert agent.twitter_api is not None

    @pytest.mark.asyncio
    async def test_execute_success(self, mock_api_clients, mock_db_session):
        """Test the successful execution of the agent."""
        agent = MarketScannerAgent()
        results = await agent.execute()

        # Check if the API methods were called
        mock_api_clients["exchange"].get_ticker_24h.assert_awaited()
        mock_api_clients["news"].fetch_latest_news.assert_awaited()
        # Note: Twitter API is called inside a loop, so we check call_count
        assert mock_api_clients["twitter"].get_sentiment_for_asset.call_count > 0

        # Check the results summary
        assert results["market_data_collected"] > 0
        assert results["news_articles_collected"] > 0
        assert results["sentiment_data_collected"] > 0
        assert not results["errors"]

        # Check if data was saved to the DB
        from src.database.models import MarketData, NewsArticle, SentimentData
        market_data_count = mock_db_session.query(MarketData).count()
        news_count = mock_db_session.query(NewsArticle).count()
        sentiment_count = mock_db_session.query(SentimentData).count()

        assert market_data_count == len(agent.monitored_assets)
        assert news_count > 0
        assert sentiment_count > 0

    @pytest.mark.asyncio
    async def test_scan_market_data_error(self, mock_api_clients):
        """Test error handling in _scan_market_data."""
        mock_api_clients["exchange"].get_ticker_24h.side_effect = Exception("Exchange API down")
        
        agent = MarketScannerAgent()
        
        with pytest.raises(Exception) as excinfo:
            await agent._scan_market_data()
        
        assert "Exchange API down" in str(excinfo.value)
