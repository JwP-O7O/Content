"""Generate and display content for existing content plans."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from src.database.connection import get_db
from src.database.models import ContentPlan, ContentFormat
from src.agents.content_creation_agent import ContentCreationAgent
from sqlalchemy.orm import joinedload

async def show_content():
    """Generate and display content for all content plans."""

    agent = ContentCreationAgent()

    print("\n" + "="*70)
    print("🎨 AI-GEGENEREERDE CONTENT")
    print("="*70 + "\n")

    with get_db() as db:
        plans = db.query(ContentPlan).options(
            joinedload(ContentPlan.insight)
        ).filter(
            ContentPlan.status == "ready"
        ).all()

        if not plans:
            print("⚠️  Geen content plans gevonden.")
            return

        for i, plan in enumerate(plans, 1):
            # Expunge to use outside session
            db.expunge(plan)
            db.expunge(plan.insight)

            print(f"\n{'─'*70}")
            print(f"📄 CONTENT PLAN #{i}")
            print(f"{'─'*70}")
            print(f"📊 Insight: {plan.insight.type.value.upper()} - {plan.insight.asset}")
            print(f"💡 Confidence: {plan.insight.confidence:.0%}")
            print(f"📱 Platform: {plan.platform}")
            print(f"📝 Format: {plan.format.value}")
            print(f"⏰ Scheduled: {plan.scheduled_for}")

            # Generate the content
            try:
                content = await agent._generate_content(plan)

                if content:
                    print(f"\n✨ GEGENEREERDE CONTENT:")
                    print("─" * 70)

                    if plan.format == ContentFormat.SINGLE_TWEET:
                        print(f"\n{content['text']}\n")
                        print(f"Lengte: {len(content['text'])} karakters")

                    elif plan.format == ContentFormat.THREAD:
                        tweets = content.get('tweets', [])
                        print(f"\nThread met {len(tweets)} tweets:\n")
                        for j, tweet in enumerate(tweets, 1):
                            print(f"{j}/🧵 {tweet}")
                            print()

                    elif plan.format == ContentFormat.TELEGRAM_MESSAGE:
                        print(f"\n{content['text']}\n")

                else:
                    print("\n❌ Content generatie gefaald")

            except Exception as e:
                print(f"\n❌ Error: {e}")

    print("\n" + "="*70)
    print("✅ Content weergave compleet!")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(show_content())
