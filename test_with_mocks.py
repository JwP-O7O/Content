"""Test the full pipeline with mock data - no external APIs needed."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from datetime import datetime, timedelta
from src.database.connection import get_db
from src.database.models import (
    MarketData, NewsArticle, SentimentData, Insight,
    InsightType, ContentPlan, ContentFormat
)
from src.orchestrator import AgentOrchestrator
from loguru import logger

def create_mock_data():
    """Create comprehensive mock data for testing."""

    print("\n" + "="*60)
    print("Creating Mock Data for Testing")
    print("="*60 + "\n")

    with get_db() as db:
        # 1. Create mock market data
        print("📊 Creating mock market data...")
        market_data_entries = [
            MarketData(
                asset="BTC",
                price=87445.11,
                volume_24h=28945632100.0,
                market_cap=1726000000000.0,
                price_change_24h=3.187,
                timestamp=datetime.utcnow() - timedelta(minutes=10)
            ),
            MarketData(
                asset="ETH",
                price=2827.89,
                volume_24h=12456789000.0,
                market_cap=340000000000.0,
                price_change_24h=2.657,
                timestamp=datetime.utcnow() - timedelta(minutes=10)
            ),
            MarketData(
                asset="XRP",
                price=2.0759,
                volume_24h=8934567800.0,
                market_cap=119000000000.0,
                price_change_24h=7.32,
                timestamp=datetime.utcnow() - timedelta(minutes=10)
            )
        ]

        for md in market_data_entries:
            db.add(md)
            print(f"  ✓ {md.asset}: ${md.price:,.2f} ({md.price_change_24h:+.2f}%)")

        db.commit()

        # 2. Create mock news articles
        print("\n📰 Creating mock news articles...")
        news_articles = [
            NewsArticle(
                title="Bitcoin Surges Past $87K as Institutional Buying Intensifies",
                url="https://example.com/btc-surge",
                source="CryptoNews",
                summary="Bitcoin reaches new highs as major institutions continue accumulating BTC. Market sentiment strongly bullish.",
                sentiment_score=0.85,
                published_at=datetime.utcnow() - timedelta(hours=2)
            ),
            NewsArticle(
                title="XRP Rally Continues With 7% Daily Gains",
                url="https://example.com/xrp-rally",
                source="CoinDesk",
                summary="XRP shows strong momentum breaking through key resistance levels with high trading volumes.",
                sentiment_score=0.78,
                published_at=datetime.utcnow() - timedelta(hours=3)
            ),
            NewsArticle(
                title="Altcoin Season? Market Rotation Signals Risk-On Sentiment",
                url="https://example.com/altcoin-season",
                source="CoinTelegraph",
                summary="Crypto market shows rotation into altcoins as BTC consolidates. DOGE, SOL leading gains.",
                sentiment_score=0.72,
                published_at=datetime.utcnow() - timedelta(hours=1)
            )
        ]

        for news in news_articles:
            db.add(news)
            print(f"  ✓ {news.title[:60]}...")

        db.commit()

        # 3. Create mock sentiment data
        print("\n💭 Creating mock sentiment data...")
        sentiment_entries = [
            SentimentData(
                asset="BTC",
                platform="twitter",
                sentiment_score=0.82,
                volume=15234,
                timestamp=datetime.utcnow() - timedelta(minutes=15)
            ),
            SentimentData(
                asset="ETH",
                platform="twitter",
                sentiment_score=0.75,
                volume=8901,
                timestamp=datetime.utcnow() - timedelta(minutes=15)
            ),
            SentimentData(
                asset="XRP",
                platform="twitter",
                sentiment_score=0.88,
                volume=12456,
                timestamp=datetime.utcnow() - timedelta(minutes=15)
            )
        ]

        for sent in sentiment_entries:
            db.add(sent)
            print(f"  ✓ {sent.asset}: {sent.sentiment_score:.2f} sentiment ({sent.volume} mentions)")

        db.commit()

        # 4. Create mock insights
        print("\n💡 Creating mock insights...")
        insights = [
            Insight(
                type=InsightType.BREAKOUT,
                asset="BTC",
                details={
                    "summary": "Bitcoin showing strong bullish momentum above $87k with significant volume increase. Market sentiment turning positive as institutional buyers accumulate. Key resistance at $90k next target.",
                    "price": 87445.11,
                    "change_24h": 3.187
                },
                confidence=0.85,
                supporting_data_ids={"market_data_id": 1, "news_article_id": 1},
                timestamp=datetime.utcnow(),
                is_published=False,
                is_exclusive=False
            ),
            Insight(
                type=InsightType.VOLUME_SPIKE,
                asset="XRP",
                details={
                    "summary": "XRP surge continues with +7.3% gain in 24h. Breaking key resistance levels. High trading volume indicates strong buyer interest. Watch for potential pullback to $2.00 support.",
                    "price": 2.0759,
                    "change_24h": 7.32
                },
                confidence=0.78,
                supporting_data_ids={"market_data_id": 3, "news_article_id": 2},
                timestamp=datetime.utcnow(),
                is_published=False,
                is_exclusive=False
            ),
            Insight(
                type=InsightType.SENTIMENT_SHIFT,
                asset="CRYPTO",
                details={
                    "summary": "Crypto market showing rotation into altcoins. DOGE +4.9%, SOL +3.9% as BTC consolidates. Total market cap holding above key support. Risk-on sentiment returning after recent correction.",
                    "assets": ["DOGE", "SOL", "BTC"]
                },
                confidence=0.82,
                supporting_data_ids={"market_data_id": 1, "news_article_id": 3},
                timestamp=datetime.utcnow(),
                is_published=False,
                is_exclusive=False
            )
        ]

        for insight in insights:
            db.add(insight)
            print(f"  ✓ {insight.type.value} for {insight.asset} (confidence: {insight.confidence:.0%})")

        db.commit()

        print("\n" + "="*60)
        print("✅ Mock Data Created Successfully!")
        print("="*60)
        print(f"\n📈 Created:")
        print(f"  • {len(market_data_entries)} market data points")
        print(f"  • {len(news_articles)} news articles")
        print(f"  • {len(sentiment_entries)} sentiment data points")
        print(f"  • {len(insights)} insights")
        print()


async def test_content_pipeline():
    """Test the content creation pipeline with mock data."""

    print("\n" + "="*60)
    print("Testing Content Creation Pipeline")
    print("="*60 + "\n")

    orchestrator = AgentOrchestrator()

    # Test Phase 1: Content Strategist + Content Creation
    print("🎯 Step 1: Running Content Strategist...")
    try:
        result = await orchestrator.content_strategist.run()
        print(f"✓ Content Strategist completed: {result}")
    except Exception as e:
        print(f"✗ Error: {e}")

    print("\n✍️  Step 2: Running Content Creation...")
    try:
        result = await orchestrator.content_creator.run()
        print(f"✓ Content Creation completed: {result}")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Show what was created
    print("\n" + "="*60)
    print("📋 Content Plans Created:")
    print("="*60 + "\n")

    with get_db() as db:
        plans = db.query(ContentPlan).all()

        if not plans:
            print("⚠️  No content plans created yet.")
        else:
            for i, plan in enumerate(plans, 1):
                platform = plan.platform if isinstance(plan.platform, str) else plan.platform.value
                format_str = plan.format.value if hasattr(plan.format, 'value') else str(plan.format)
                print(f"\n{i}. {format_str.upper()} for {platform}")
                print(f"   Status: {plan.status}")
                if hasattr(plan, 'generated_content') and plan.generated_content:
                    content = plan.generated_content[:200] + "..." if len(plan.generated_content) > 200 else plan.generated_content
                    print(f"   Content: {content}")
                if hasattr(plan, 'scheduled_time') and plan.scheduled_time:
                    print(f"   Scheduled: {plan.scheduled_time}")
                elif hasattr(plan, 'scheduled_for') and plan.scheduled_for:
                    print(f"   Scheduled: {plan.scheduled_for}")

    print("\n" + "="*60)
    print("✅ Test Complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Step 1: Create mock data
    create_mock_data()

    # Step 2: Test pipeline
    print("\n⏳ Starting pipeline test in 2 seconds...\n")
    import time
    time.sleep(2)

    asyncio.run(test_content_pipeline())
