"""Create test data for content generation testing."""

import sys
import os
# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from loguru import logger

from config.config import settings
from src.database.models import Insight, MarketData, NewsArticle, InsightType

async def create_test_insights():
    """Insert sample insights to test content generation."""

    # Create async engine
    engine = create_async_engine(settings.database_url.replace("postgresql://", "postgresql+asyncpg://"))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("="*60)
    print("Creating Test Data for Content Generation")
    print("="*60)

    async with async_session() as session:
        # Get recent market data to link insights to
        from sqlalchemy import select
        result = await session.execute(
            select(MarketData).order_by(MarketData.created_at.desc()).limit(1)
        )
        recent_market_data = result.scalar_one_or_none()

        if not recent_market_data:
            print("❌ No market data found. Run market scan first!")
            return

        print(f"\n✓ Found market data: {recent_market_data.asset} at ${recent_market_data.price}")

        # Get recent news
        result = await session.execute(
            select(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(1)
        )
        recent_news = result.scalar_one_or_none()

        if recent_news:
            print(f"✓ Found news article: {recent_news.title[:50]}...")

        # Create sample insights using valid InsightType enum values
        test_insights = [
            {
                "type": InsightType.BREAKOUT,
                "asset": "BTC",
                "details": {
                    "summary": "Bitcoin showing strong bullish momentum above $87k with significant volume increase. "
                              "Market sentiment turning positive as institutional buyers accumulate. "
                              "Key resistance at $90k next target.",
                    "price": 87445.11,
                    "change_24h": 3.187
                },
                "confidence": 0.85,
                "supporting_data_ids": {"market_data_id": recent_market_data.id, "news_article_id": recent_news.id if recent_news else None}
            },
            {
                "type": InsightType.VOLUME_SPIKE,
                "asset": "XRP",
                "details": {
                    "summary": "XRP surge continues with +7.3% gain in 24h. Breaking key resistance levels. "
                              "High trading volume indicates strong buyer interest. "
                              "Watch for potential pullback to $2.00 support.",
                    "price": 2.0759,
                    "change_24h": 7.32
                },
                "confidence": 0.78,
                "supporting_data_ids": {"market_data_id": recent_market_data.id, "news_article_id": recent_news.id if recent_news else None}
            },
            {
                "type": InsightType.SENTIMENT_SHIFT,
                "asset": "MULTI",
                "details": {
                    "summary": "Crypto market showing rotation into altcoins. DOGE +4.9%, SOL +3.9% as BTC consolidates. "
                              "Total market cap holding above key support. "
                              "Risk-on sentiment returning after recent correction.",
                    "assets": ["DOGE", "SOL", "BTC"]
                },
                "confidence": 0.82,
                "supporting_data_ids": {"market_data_id": recent_market_data.id}
            },
            {
                "type": InsightType.BREAKDOWN,
                "asset": "MATIC",
                "details": {
                    "summary": "MATIC showing weakness with -0.3% decline while market rallies. "
                              "Underperformance vs peers may signal further downside risk. "
                              "Monitor key support at $0.35.",
                    "price": 0.3794,
                    "change_24h": -0.289
                },
                "confidence": 0.72,
                "supporting_data_ids": {"market_data_id": recent_market_data.id}
            },
            {
                "type": InsightType.TECHNICAL_PATTERN,
                "asset": "ETH",
                "details": {
                    "summary": "Ethereum gaining strength at $2,827 with steady volume. "
                              "ETH/BTC ratio improving, suggesting rotation into ETH. "
                              "Target $3,000 psychological resistance in coming sessions.",
                    "price": 2827.89,
                    "change_24h": 2.657
                },
                "confidence": 0.80,
                "supporting_data_ids": {"market_data_id": recent_market_data.id}
            }
        ]

        insights_created = 0

        for insight_data in test_insights:
            insight = Insight(
                type=insight_data["type"],
                asset=insight_data["asset"],
                details=insight_data["details"],
                confidence=insight_data["confidence"],
                supporting_data_ids=insight_data["supporting_data_ids"],
                timestamp=datetime.utcnow(),
                is_published=False,
                is_exclusive=False
            )
            session.add(insight)
            insights_created += 1
            print(f"\n✓ Created {insight_data['type'].value} insight for {insight_data['asset']}: {insight_data['details']['summary'][:60]}...")

        await session.commit()

        print(f"\n{'='*60}")
        print(f"✅ Test Data Created Successfully!")
        print(f"{'='*60}")
        print(f"Insights created: {insights_created}")
        print(f"\nYou can now run content creation pipeline to generate content from these insights.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_test_insights())
