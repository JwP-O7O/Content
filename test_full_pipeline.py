"""Test the full content creation pipeline end-to-end."""

import asyncio
from loguru import logger
from src.orchestrator import AgentOrchestrator

async def test_full_pipeline():
    """Test complete pipeline: Scan → Analyze → Create → Publish."""

    print("="*60)
    print("Testing Full Content Pipeline End-to-End")
    print("="*60)

    # Initialize orchestrator
    orchestrator = AgentOrchestrator()

    # Run full pipeline
    print("\n🚀 Running Full Pipeline...")
    print("   (Market Scan → Analysis → Strategy → Creation → Publishing)")
    print("-"*60)

    result = await orchestrator.run_full_pipeline()

    print("\n" + "="*60)
    print("📊 Pipeline Results:")
    print("="*60)

    agents = result.get("agents", {})

    # Market scan results
    if "market_scanner" in agents:
        scan = agents["market_scanner"]
        print(f"\n1️⃣  MARKET SCAN:")
        print(f"   ✓ Market data: {scan.get('market_data_collected', 0)} assets")
        print(f"   ✓ News articles: {scan.get('news_articles_collected', 0)}")
        print(f"   ✓ Sentiment data: {scan.get('sentiment_data_collected', 0)}")

    # Analysis results
    if "analysis" in agents:
        analysis = agents["analysis"]
        if analysis.get("status") == "skipped":
            print(f"\n2️⃣  ANALYSIS:")
            print(f"   ⚠️  Skipped: {analysis.get('reason', 'N/A')}")
        else:
            print(f"\n2️⃣  ANALYSIS:")
            print(f"   ✓ Insights generated: {analysis.get('insights_generated', 0)}")

    # Strategy results
    if "content_strategist" in agents:
        strategy = agents["content_strategist"]
        print(f"\n3️⃣  CONTENT STRATEGY:")
        print(f"   ✓ Insights reviewed: {strategy.get('insights_reviewed', 0)}")
        print(f"   ✓ Plans created: {strategy.get('content_plans_created', 0)}")
        print(f"   ✓ Exclusive plans: {strategy.get('exclusive_content_plans', 0)}")
        print(f"   ✓ Skipped: {strategy.get('skipped_insights', 0)}")

    # Creation results
    if "content_creator" in agents:
        creation = agents["content_creator"]
        print(f"\n4️⃣  CONTENT CREATION:")
        print(f"   ✓ Content created: {creation.get('content_created', 0)}")
        print(f"   ✓ Tweets: {creation.get('tweets', 0)}")
        print(f"   ✓ Threads: {creation.get('threads', 0)}")
        print(f"   ✓ Telegram: {creation.get('telegram_messages', 0)}")
        if creation.get('errors'):
            print(f"   ⚠️  Errors: {len(creation['errors'])}")

    # Publishing results
    if "publisher" in agents:
        publishing = agents["publisher"]
        print(f"\n5️⃣  PUBLISHING:")
        print(f"   ✓ Published: {publishing.get('content_published', 0)}")
        print(f"   ✓ Twitter posts: {publishing.get('twitter_posts', 0)}")
        print(f"   ✓ Telegram posts: {publishing.get('telegram_posts', 0)}")
        print(f"   ⏳ Awaiting approval: {publishing.get('awaiting_approval', 0)}")
        if publishing.get('errors'):
            print(f"   ⚠️  Errors: {len(publishing['errors'])}")

    print("\n" + "="*60)
    print("✅ Full Pipeline Test Complete!")
    print("="*60)

    return result

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
