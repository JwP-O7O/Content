"""System health check for all components."""

import asyncio
from datetime import datetime
from loguru import logger

async def system_health_check():
    """Comprehensive system health check."""

    print("="*60)
    print("SYSTEM HEALTH CHECK")
    print("="*60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    results = {
        "database": False,
        "llm_client": False,
        "agents": {},
        "api_keys": {},
        "overall": "UNKNOWN"
    }

    # 1. Database connectivity
    print("\n1️⃣  DATABASE CONNECTIVITY")
    print("-"*60)
    try:
        from src.database.connection import get_db
        from sqlalchemy import text

        with get_db() as db:
            db.execute(text("SELECT 1"))
            print("   ✅ PostgreSQL connection: OK")
            results["database"] = True
    except Exception as e:
        print(f"   ❌ Database error: {e}")

    # 2. LLM Client
    print("\n2️⃣  LLM CLIENT")
    print("-"*60)
    try:
        from src.utils.llm_client import llm_client

        # Quick test
        response = llm_client.generate(
            prompt="Say 'OK' if you can read this.",
            model="gemini",
            max_tokens=10
        )
        if response and len(response) > 0:
            print(f"   ✅ Gemini API: OK (active: {llm_client.get_active_gemini_key()})")
            results["llm_client"] = True
        else:
            print("   ⚠️  Gemini API: Empty response")
    except Exception as e:
        print(f"   ❌ LLM Client error: {e}")

    # 3. Agent Initialization
    print("\n3️⃣  AGENT STATUS")
    print("-"*60)
    try:
        from src.orchestrator import AgentOrchestrator

        orchestrator = AgentOrchestrator()

        agents_to_check = [
            ("MarketScanner", orchestrator.market_scanner),
            ("ContentStrategist", orchestrator.content_strategist),
            ("ContentCreator", orchestrator.content_creator),
            ("Publisher", orchestrator.publisher),
            ("Analytics", orchestrator.analytics_agent),
        ]

        for name, agent in agents_to_check:
            if agent:
                print(f"   ✅ {name}: Initialized")
                results["agents"][name] = True
            else:
                print(f"   ❌ {name}: Not initialized")
                results["agents"][name] = False

        if orchestrator.analysis_agent is None:
            print(f"   ⚠️  AnalysisAgent: Skipped (pandas unavailable)")
            results["agents"]["Analysis"] = "skipped"

    except Exception as e:
        print(f"   ❌ Agent initialization error: {e}")

    # 4. API Keys Status
    print("\n4️⃣  API KEYS")
    print("-"*60)
    try:
        from config.config import settings

        # Check Gemini
        if settings.google_api_key and not settings.google_api_key.startswith("test"):
            print("   ✅ Gemini API (primary): Configured")
            results["api_keys"]["gemini_primary"] = True
        else:
            print("   ❌ Gemini API (primary): Not configured")

        if settings.google_api_key_backup:
            print("   ✅ Gemini API (backup): Configured")
            results["api_keys"]["gemini_backup"] = True
        else:
            print("   ⚠️  Gemini API (backup): Not configured")

        # Check Anthropic
        if settings.anthropic_api_key and not settings.anthropic_api_key.startswith("sk-ant-test"):
            print("   ✅ Anthropic API: Configured (no credits)")
            results["api_keys"]["anthropic"] = "no_credits"
        else:
            print("   ❌ Anthropic API: Not configured")

        # Twitter & Telegram (test keys expected)
        print("   ⚠️  Twitter API: Test keys (not for production)")
        print("   ⚠️  Telegram API: Test keys (not for production)")

    except Exception as e:
        print(f"   ❌ API key check error: {e}")

    # 5. Database Statistics
    print("\n5️⃣  DATABASE STATISTICS")
    print("-"*60)
    try:
        from src.database.connection import get_db
        from src.database.models import MarketData, NewsArticle, Insight, ContentPlan
        from sqlalchemy import func

        with get_db() as db:
            market_data = db.query(func.count(MarketData.id)).scalar()
            news = db.query(func.count(NewsArticle.id)).scalar()
            insights = db.query(func.count(Insight.id)).scalar()
            plans = db.query(func.count(ContentPlan.id)).scalar()

            print(f"   Market Data: {market_data} entries")
            print(f"   News Articles: {news} entries")
            print(f"   Insights: {insights} entries")
            print(f"   Content Plans: {plans} entries")

    except Exception as e:
        print(f"   ❌ Database stats error: {e}")

    # Overall assessment
    print("\n" + "="*60)
    print("OVERALL HEALTH:")
    print("="*60)

    critical_systems = [
        results["database"],
        results["llm_client"],
        len([a for a in results["agents"].values() if a is True]) >= 3
    ]

    if all(critical_systems):
        results["overall"] = "HEALTHY"
        print("   🟢 Status: HEALTHY")
        print("   All critical systems operational")
    elif any(critical_systems):
        results["overall"] = "DEGRADED"
        print("   🟡 Status: DEGRADED")
        print("   Some systems not fully operational")
    else:
        results["overall"] = "CRITICAL"
        print("   🔴 Status: CRITICAL")
        print("   Critical systems offline")

    print("\n" + "="*60)

    return results

if __name__ == "__main__":
    asyncio.run(system_health_check())
