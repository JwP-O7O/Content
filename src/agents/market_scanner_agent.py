"""MarketScannerAgent - Continuously scans markets for data."""

import asyncio

from config.config import settings
from src.agents.base_agent import BaseAgent
from src.api_integrations.exchange_api import ExchangeAPI
from src.api_integrations.news_api import NewsAPI
from src.api_integrations.twitter_api import TwitterAPI
from src.database.connection import get_db
from src.database.models import MarketData, NewsArticle, SentimentData


class MarketScannerAgent(BaseAgent):
    """
    The Market Scanner Agent continuously scans the crypto market for data.

    Responsibilities:
    - Fetch price and volume data from exchanges
    - Collect news articles from various sources
    - Monitor social media sentiment
    - Store all data in the database for analysis
    """

    def __init__(self):
        """Initialize the MarketScannerAgent."""
        super().__init__("MarketScannerAgent")

        # Initialize API clients
        self.exchange_api = ExchangeAPI(
            api_key=settings.binance_api_key,
            api_secret=settings.binance_api_secret
        )
        self.news_api = NewsAPI()

        # Initialize Twitter API for sentiment if available
        try:
            self.twitter_api = TwitterAPI(
                api_key=settings.twitter_api_key,
                api_secret=settings.twitter_api_secret,
                access_token=settings.twitter_access_token,
                access_token_secret=settings.twitter_access_token_secret,
                bearer_token=settings.twitter_bearer_token
            )
        except:
            self.log_warning("Twitter API not configured - sentiment scanning disabled")
            self.twitter_api = None

        # Assets to monitor
        self.monitored_assets = [
            "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT",
            "ADAUSDT", "XRPUSDT", "DOGEUSDT", "MATICUSDT"
        ]

    async def execute(self) -> dict:
        """
        Execute the market scanning process.

        Returns:
            Dictionary with scan results summary
        """
        self.log_info("Starting market scan...")

        results = {
            "market_data_collected": 0,
            "news_articles_collected": 0,
            "sentiment_data_collected": 0,
            "errors": []
        }

        # Run all scanning tasks in parallel
        tasks = [
            self._scan_market_data(),
            self._scan_news(),
            self._scan_sentiment()
        ]

        scan_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, result in enumerate(scan_results):
            if isinstance(result, Exception):
                results["errors"].append(str(result))
            else:
                if i == 0:  # Market data
                    results["market_data_collected"] = result
                elif i == 1:  # News
                    results["news_articles_collected"] = result
                elif i == 2:  # Sentiment
                    results["sentiment_data_collected"] = result

        self.log_info(
            f"Market scan complete: "
            f"{results['market_data_collected']} market data points, "
            f"{results['news_articles_collected']} news articles, "
            f"{results['sentiment_data_collected']} sentiment data points"
        )

        return results

    async def _scan_market_data(self) -> int:
        """
        Scan and store market data for monitored assets.

        Returns:
            Number of data points collected
        """
        self.log_info("Scanning market data...")
        count = 0

        try:
            with get_db() as db:
                # Fetch data for each monitored asset
                for symbol in self.monitored_assets:
                    ticker_data = await self.exchange_api.get_ticker_24h(symbol)

                    if ticker_data:
                        # Extract asset name (e.g., BTC from BTCUSDT)
                        asset = symbol.replace("USDT", "")

                        market_data = MarketData(
                            asset=asset,
                            price=ticker_data["price"],
                            volume_24h=ticker_data["volume_24h"],
                            price_change_24h=ticker_data["price_change_24h"],
                            raw_data=ticker_data["raw_data"]
                        )

                        db.add(market_data)
                        count += 1

                        # Small delay to avoid rate limits
                        await asyncio.sleep(0.1)

                db.commit()

            # Also fetch top gainers/losers
            gainers_losers = await self.exchange_api.get_top_gainers_losers(limit=10)

            self.log_info(
                f"Top gainer: {gainers_losers['gainers'][0]['symbol']} "
                f"(+{gainers_losers['gainers'][0]['change_percent']:.2f}%)"
            )

        except Exception as e:
            self.log_error(f"Error scanning market data: {e}")
            raise

        return count

    async def _scan_news(self) -> int:
        """
        Scan and store crypto news articles.

        Returns:
            Number of articles collected
        """
        self.log_info("Scanning news articles...")
        count = 0

        try:
            # Fetch latest news
            articles = await self.news_api.fetch_latest_news(max_articles=20)

            with get_db() as db:
                for article_data in articles:
                    # Check if article already exists
                    existing = db.query(NewsArticle).filter(
                        NewsArticle.url == article_data["url"]
                    ).first()

                    if not existing:
                        article = NewsArticle(
                            title=article_data["title"],
                            url=article_data["url"],
                            source=article_data["source"],
                            published_at=article_data["published_at"],
                            content=article_data["content"],
                            summary=article_data["summary"]
                        )

                        db.add(article)
                        count += 1

                db.commit()

        except Exception as e:
            self.log_error(f"Error scanning news: {e}")
            raise

        return count

    async def _scan_sentiment(self) -> int:
        """
        Scan and store social media sentiment data.

        Returns:
            Number of sentiment data points collected
        """
        if not self.twitter_api:
            return 0

        self.log_info("Scanning social sentiment...")
        count = 0

        try:
            with get_db() as db:
                # Get sentiment for major assets
                major_assets = ["BTC", "ETH", "SOL", "XRP"]

                for asset in major_assets:
                    sentiment_data = self.twitter_api.get_sentiment_for_asset(asset)

                    if sentiment_data["volume"] > 0:
                        sentiment = SentimentData(
                            platform="twitter",
                            asset=asset,
                            sentiment_score=0,  # Will be enhanced later with NLP
                            volume=sentiment_data["volume"],
                            raw_data=sentiment_data
                        )

                        db.add(sentiment)
                        count += 1

                    # Rate limit protection
                    await asyncio.sleep(1)

                db.commit()

        except Exception as e:
            self.log_error(f"Error scanning sentiment: {e}")
            raise

        return count

    async def scan_specific_asset(self, asset: str) -> dict:
        """
        Perform a targeted scan for a specific asset.

        Args:
            asset: Asset symbol (e.g., BTC, ETH)

        Returns:
            Dictionary with scan results for the asset
        """
        self.log_info(f"Performing targeted scan for {asset}...")

        results = {}

        # Get market data
        symbol = f"{asset}USDT"
        ticker_data = await self.exchange_api.get_ticker_24h(symbol)
        results["market_data"] = ticker_data

        # Get news about the asset
        news = await self.news_api.search_news(asset, days_back=3)
        results["news"] = news

        # Get sentiment
        if self.twitter_api:
            sentiment = self.twitter_api.get_sentiment_for_asset(asset)
            results["sentiment"] = sentiment

        return results
