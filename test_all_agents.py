"""Test all agents in the system with mock data."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from datetime import datetime, timedelta
from src.database.connection import get_db
from src.database.models import (
    PublishedContent, CommunityUser, UserInteraction, UserTier,
    ContentPlan, ABTest
)
from src.orchestrator import AgentOrchestrator

async def test_all_phases():
    """Test agents from all 4 phases."""

    print("\n" + "="*70)
    print("🚀 TESTING ALL AGENTS - 4 PHASES")
    print("="*70 + "\n")

    orchestrator = AgentOrchestrator()

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 1: Content Creation Pipeline (Already tested)
    # ═══════════════════════════════════════════════════════════════════
    print("📍 PHASE 1: Content Creation Pipeline")
    print("─" * 70)
    print("✅ Market Scanner, Content Strategist, Content Creator (already tested)")
    print()

    # Simulate publishing some content
    print("📤 Simulating publishing content...")

    with get_db() as db:
        # Get content plans
        plans = db.query(ContentPlan).filter(ContentPlan.status == "ready").limit(2).all()

        for plan in plans:
            # Create published content entry
            published = PublishedContent(
                content_plan_id=plan.id,
                platform=plan.platform,
                content_text=f"Mock published content for plan {plan.id}",
                post_url=f"https://twitter.com/mock/{plan.id}",
                post_id=f"mock_{plan.id}",
                published_at=datetime.utcnow(),
                views=1250 + (plan.id * 100),
                likes=85 + (plan.id * 10),
                comments=12 + plan.id,
                shares=8 + plan.id,
                engagement_rate=0.068
            )
            db.add(published)
            print(f"  ✓ Published content plan #{plan.id}")

        db.commit()

    print()

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 2: Audience Building
    # ═══════════════════════════════════════════════════════════════════
    print("\n📍 PHASE 2: Audience Building")
    print("─" * 70)

    # Create mock community users
    print("👥 Creating mock community users...")
    with get_db() as db:
        users = [
            CommunityUser(
                twitter_id="user_001",
                twitter_username="crypto_whale_88",
                tier=UserTier.FREE,
                engagement_score=72,
                first_seen=datetime.utcnow() - timedelta(days=30)
            ),
            CommunityUser(
                twitter_id="user_002",
                twitter_username="btc_analyst",
                tier=UserTier.FREE,
                engagement_score=85,
                first_seen=datetime.utcnow() - timedelta(days=45)
            ),
            CommunityUser(
                twitter_id="user_003",
                twitter_username="crypto_newbie",
                tier=UserTier.FREE,
                engagement_score=45,
                first_seen=datetime.utcnow() - timedelta(days=7)
            )
        ]

        for user in users:
            db.add(user)
        db.commit()
        print(f"  ✓ Created {len(users)} mock users")

    # Create mock interactions
    print("💬 Creating mock user interactions...")
    with get_db() as db:
        published = db.query(PublishedContent).first()
        if published:
            interactions = [
                UserInteraction(
                    user_id=1,
                    content_id=published.id,
                    interaction_type="like",
                    platform="twitter",
                    engagement_value=1.0,
                    timestamp=datetime.utcnow() - timedelta(hours=2)
                ),
                UserInteraction(
                    user_id=1,
                    content_id=published.id,
                    interaction_type="retweet",
                    platform="twitter",
                    engagement_value=3.0,
                    timestamp=datetime.utcnow() - timedelta(hours=1)
                ),
                UserInteraction(
                    user_id=2,
                    content_id=published.id,
                    interaction_type="reply",
                    platform="twitter",
                    interaction_metadata={"text": "Great analysis! When's the next update?"},
                    engagement_value=5.0,
                    timestamp=datetime.utcnow() - timedelta(minutes=30)
                ),
            ]
            for interaction in interactions:
                db.add(interaction)
            db.commit()
            print(f"  ✓ Created {len(interactions)} mock interactions")

    # Test Analytics Agent
    print("\n📊 Testing Analytics Agent...")
    try:
        result = await orchestrator.analytics_agent.run()
        print(f"  ✓ Analytics Agent: {result}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 3: Monetization
    # ═══════════════════════════════════════════════════════════════════
    print("\n📍 PHASE 3: Monetization")
    print("─" * 70)

    # Test Conversion Agent
    print("💰 Testing Conversion Agent...")
    try:
        result = await orchestrator.conversion_agent.run()
        print(f"  ✓ Conversion Agent: {result}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 4: Self-Learning & Optimization
    # ═══════════════════════════════════════════════════════════════════
    print("\n📍 PHASE 4: Self-Learning & Optimization")
    print("─" * 70)

    # Test Performance Analytics
    print("📈 Testing Performance Analytics Agent...")
    try:
        result = await orchestrator.performance_analytics.run()
        print(f"  ✓ Performance Analytics: {result}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # Test A/B Testing Agent
    print("\n🧪 Testing A/B Testing Agent...")
    try:
        result = await orchestrator.ab_testing.run()
        print(f"  ✓ A/B Testing Agent: {result}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # ═══════════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)

    with get_db() as db:
        content_plans = db.query(ContentPlan).count()
        published = db.query(PublishedContent).count()
        users = db.query(CommunityUser).count()
        ab_tests = db.query(ABTest).count()

        print(f"\n✅ System Status:")
        print(f"  • Content Plans: {content_plans}")
        print(f"  • Published Content: {published}")
        print(f"  • Community Users: {users}")
        print(f"  • A/B Tests: {ab_tests}")

    print("\n" + "="*70)
    print("✅ ALL TESTS COMPLETE!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_all_phases())
