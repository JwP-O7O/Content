"""Test analytics generation and KPI dashboard."""

import asyncio
from loguru import logger
from src.agents.analytics_agent import AnalyticsAgent

async def test_analytics():
    """Test analytics report generation."""

    print("="*60)
    print("Testing Analytics Report Generation")
    print("="*60)

    # Initialize analytics agent
    analytics_agent = AnalyticsAgent()

    print("\n📊 Generating Analytics Report...")
    print("-"*60)

    result = await analytics_agent.run()

    print("\n" + "="*60)
    print("📈 Analytics Results:")
    print("="*60)

    if "reports" in result:
        reports = result["reports"]
        print(f"\n✓ Reports generated: {len(reports)}")

        for i, report in enumerate(reports[:3], 1):  # Show first 3
            print(f"\n{i}. {report.get('title', 'Untitled Report')}")
            print(f"   Type: {report.get('type', 'N/A')}")
            print(f"   Period: {report.get('period', 'N/A')}")
            if 'metrics' in report:
                print(f"   Metrics: {len(report['metrics'])} tracked")

    if "engagement_summary" in result:
        engagement = result["engagement_summary"]
        print(f"\n📱 Engagement Summary:")
        print(f"   Total interactions: {engagement.get('total_interactions', 0)}")
        print(f"   Avg engagement rate: {engagement.get('avg_engagement_rate', 0):.2%}")

    if "content_performance" in result:
        performance = result["content_performance"]
        print(f"\n📝 Content Performance:")
        print(f"   Top performing: {performance.get('top_performing', 'N/A')}")
        print(f"   Total published: {performance.get('total_published', 0)}")

    if "errors" in result and result["errors"]:
        print(f"\n⚠️  Errors: {len(result['errors'])}")
        for err in result["errors"][:3]:
            print(f"   - {err}")

    print("\n" + "="*60)
    print("✅ Analytics Test Complete!")
    print("="*60)

    return result

async def view_kpi_dashboard():
    """View KPI dashboard with current metrics."""

    print("\n" + "="*60)
    print("KPI Dashboard")
    print("="*60)

    from src.database.connection import get_db
    from src.database.models import (
        MarketData, NewsArticle, Insight,
        ContentPlan, PublishedContent
    )
    from sqlalchemy import func

    with get_db() as db:
        # Count records
        market_count = db.query(func.count(MarketData.id)).scalar()
        news_count = db.query(func.count(NewsArticle.id)).scalar()
        insight_count = db.query(func.count(Insight.id)).scalar()
        plan_count = db.query(func.count(ContentPlan.id)).scalar()
        published_count = db.query(func.count(PublishedContent.id)).scalar()

        # Content plan statuses
        pending = db.query(func.count(ContentPlan.id)).filter(
            ContentPlan.status == "pending"
        ).scalar()
        ready = db.query(func.count(ContentPlan.id)).filter(
            ContentPlan.status == "ready"
        ).scalar()
        awaiting = db.query(func.count(ContentPlan.id)).filter(
            ContentPlan.status == "awaiting_approval"
        ).scalar()

        print(f"\n📊 Data Collection:")
        print(f"   Market Data Points: {market_count}")
        print(f"   News Articles: {news_count}")
        print(f"   Insights Generated: {insight_count}")

        print(f"\n📝 Content Pipeline:")
        print(f"   Total Plans: {plan_count}")
        print(f"   ├─ Pending: {pending}")
        print(f"   ├─ Ready: {ready}")
        print(f"   └─ Awaiting Approval: {awaiting}")
        print(f"   Published: {published_count}")

        # Insight types breakdown
        from sqlalchemy import distinct
        insight_types = db.query(
            Insight.type,
            func.count(Insight.id).label('count')
        ).group_by(Insight.type).all()

        if insight_types:
            print(f"\n🔍 Insights by Type:")
            for itype, count in insight_types:
                print(f"   {itype.value}: {count}")

        # Content formats
        formats = db.query(
            ContentPlan.format,
            func.count(ContentPlan.id).label('count')
        ).group_by(ContentPlan.format).all()

        if formats:
            print(f"\n📱 Content Formats:")
            for fmt, count in formats:
                print(f"   {fmt.value}: {count}")

        # Platform distribution
        platforms = db.query(
            ContentPlan.platform,
            func.count(ContentPlan.id).label('count')
        ).group_by(ContentPlan.platform).all()

        if platforms:
            print(f"\n🌐 Platform Distribution:")
            for platform, count in platforms:
                print(f"   {platform}: {count}")

    print("\n" + "="*60)
    print("✅ KPI Dashboard Complete!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_analytics())
    asyncio.run(view_kpi_dashboard())
