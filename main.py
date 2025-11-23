"""Main entry point for the Content Creator system."""

import asyncio
import sys

from loguru import logger

from src.orchestrator import AgentOrchestrator
from src.scheduler import ContentCreatorScheduler
from src.utils.logger import setup_logger


def print_banner():
    """Print the system banner."""
    banner = """
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║     Content Creator - Autonomous AI Agent System        ║
║                                                          ║
║     An autonomous crypto content & community platform   ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_menu():
    """Print the main menu."""
    menu = """
Choose an option:

PHASE 1 - Core Pipeline:
1. Run Full Pipeline (Scan → Analyze → Create → Publish)
2. Run Market Scan Only
3. Run Analysis Only
4. Run Content Creation Pipeline

PHASE 2 - Audience Building:
5. Run Full Phase 2 Pipeline (All agents including engagement)
6. Run Engagement Pipeline (Monitor & Interact)
7. Generate Analytics Report
8. View KPI Dashboard

PHASE 3 - Monetization:
9. Run Full Phase 3 Pipeline (Including monetization)
10. Run Monetization Pipeline Only
11. View Conversion Metrics
12. View Subscription Stats

PHASE 4 - Optimization & Self-Learning:
13. Run Full Phase 4 Pipeline (Self-optimizing system)
14. Run Optimization Pipeline Only
15. View A/B Test Results
16. View System Health Score
17. Generate Learning Report

MANAGEMENT:
18. Start Scheduler (Automated Continuous Operation)
19. View Pending Approvals
20. Exit

Enter choice (1-20): """
    return input(menu)


async def run_interactive_mode():
    """Run the system in interactive mode."""
    setup_logger()
    print_banner()

    orchestrator = AgentOrchestrator()
    scheduler = None

    while True:
        choice = print_menu()

        try:
            if choice == "1":
                logger.info("Running full pipeline...")
                results = await orchestrator.run_full_pipeline()
                logger.info(f"Pipeline results: {results}")

            elif choice == "2":
                logger.info("Running market scan...")
                results = await orchestrator.run_market_scan_only()
                logger.info(f"Scan results: {results}")

            elif choice == "3":
                logger.info("Running analysis...")
                results = await orchestrator.run_analysis_only()
                logger.info(f"Analysis results: {results}")

            elif choice == "4":
                logger.info("Running content creation pipeline...")
                results = await orchestrator.run_content_creation_pipeline()
                logger.info(f"Content creation results: {results}")

            elif choice == "5":
                logger.info("Running full Phase 2 pipeline...")
                results = await orchestrator.run_full_pipeline_phase2()
                logger.info(f"Phase 2 pipeline results: {results}")

            elif choice == "6":
                logger.info("Running engagement pipeline...")
                results = await orchestrator.run_engagement_pipeline()
                logger.info(f"Engagement results: {results}")

            elif choice == "7":
                logger.info("Generating analytics report...")
                report = await orchestrator.generate_analytics_report(days=7)
                print("\n" + report)

            elif choice == "8":
                logger.info("Loading KPI dashboard...")
                kpis = await orchestrator.get_kpi_dashboard()

                print("\n" + "="*60)
                print("KPI DASHBOARD")
                print("="*60)
                print("\nLast 24 Hours:")
                print(f"  Insights Generated:  {kpis['insights_generated_24h']}")
                print(f"  Content Published:   {kpis['content_published_24h']}")
                print("\nLast 7 Days:")
                print(f"  Insights Generated:  {kpis['insights_generated_7d']}")
                print(f"  Content Published:   {kpis['content_published_7d']}")
                print(f"  Total Engagement:    {kpis['total_engagement_7d']}")
                print(f"  Avg Engagement Rate: {kpis['avg_engagement_rate_7d']:.2%}")
                print("\nPipeline:")
                print(f"  Content in Queue:    {kpis['content_in_pipeline']}")
                print(f"\nLast Updated: {kpis['last_updated']}")
                print("="*60 + "\n")

            elif choice == "9":
                logger.info("Running full Phase 3 pipeline...")
                results = await orchestrator.run_full_pipeline_phase3()
                logger.info(f"Phase 3 pipeline results: {results}")

            elif choice == "10":
                logger.info("Running monetization pipeline...")
                results = await orchestrator.run_monetization_pipeline()
                logger.info(f"Monetization results: {results}")

            elif choice == "11":
                logger.info("Loading conversion metrics...")
                metrics = await orchestrator.conversion_agent.get_conversion_metrics(days=30)

                print("\n" + "="*60)
                print("CONVERSION METRICS (Last 30 Days)")
                print("="*60)
                print(f"\nTotal DM Attempts:   {metrics['total_dm_attempts']}")
                print(f"Conversions:         {metrics['conversions']}")
                print(f"Conversion Rate:     {metrics['conversion_rate']:.2%}")
                print(f"Open Rate:           {metrics['open_rate']:.2%}")
                print(f"Click Rate:          {metrics['click_rate']:.2%}")
                print("="*60 + "\n")

            elif choice == "12":
                logger.info("Loading subscription stats...")

                from src.database.connection import get_db
                from src.database.models import CommunityUser, Subscription, UserTier

                with get_db() as db:
                    total_users = db.query(CommunityUser).count()
                    paying_users = db.query(CommunityUser).filter(
                        CommunityUser.tier != UserTier.FREE
                    ).count()

                    active_subs = db.query(Subscription).filter(
                        Subscription.status == "active"
                    ).count()

                    # Count by tier
                    basic = db.query(CommunityUser).filter(
                        CommunityUser.tier == UserTier.BASIC
                    ).count()
                    premium = db.query(CommunityUser).filter(
                        CommunityUser.tier == UserTier.PREMIUM
                    ).count()
                    vip = db.query(CommunityUser).filter(
                        CommunityUser.tier == UserTier.VIP
                    ).count()

                print("\n" + "="*60)
                print("SUBSCRIPTION STATS")
                print("="*60)
                print(f"\nTotal Users:         {total_users}")
                print(f"Paying Members:      {paying_users}")
                print(f"Conversion Rate:     {(paying_users/total_users*100):.1f}%" if total_users > 0 else "N/A")
                print(f"\nActive Subscriptions: {active_subs}")
                print("\nBy Tier:")
                print(f"  Basic:   {basic}")
                print(f"  Premium: {premium}")
                print(f"  VIP:     {vip}")
                print("="*60 + "\n")

            elif choice == "13":
                logger.info("Running full Phase 4 pipeline...")
                results = await orchestrator.run_full_pipeline_phase4()
                logger.info(f"Phase 4 pipeline results: {results}")

            elif choice == "14":
                logger.info("Running optimization pipeline...")
                results = await orchestrator.run_optimization_pipeline()
                logger.info(f"Optimization results: {results}")

            elif choice == "15":
                logger.info("Loading A/B test results...")

                # Get active tests
                from src.database.connection import get_db
                from src.database.models import ABTest, TestStatus

                with get_db() as db:
                    tests = db.query(ABTest).filter(
                        ABTest.status == TestStatus.COMPLETED
                    ).order_by(ABTest.completed_at.desc()).limit(10).all()

                    print("\n" + "="*60)
                    print("A/B TEST RESULTS (Last 10 Completed)")
                    print("="*60)

                    if not tests:
                        print("\nNo completed tests yet")
                    else:
                        for test in tests:
                            print(f"\nTest: {test.test_name}")
                            print(f"Variable: {test.variable_being_tested}")
                            print(f"Status: {test.status.value}")
                            print(f"Improvement: {test.improvement_percentage:.1f}%" if test.improvement_percentage else "N/A")
                            print(f"Confidence: {test.confidence_level:.0%}" if test.confidence_level else "N/A")
                            print(f"Completed: {test.completed_at}")

                    print("="*60 + "\n")

            elif choice == "16":
                logger.info("Calculating system health score...")
                health = await orchestrator.get_system_health()

                print("\n" + "="*60)
                print("SYSTEM HEALTH SCORE")
                print("="*60)
                print(f"\nOverall Health: {health['health_score']}/100 ({health['status'].upper()})")
                print("\nComponent Scores:")
                for component, score in health["components"].items():
                    print(f"  {component.replace('_', ' ').title()}: {score}/100")
                print(f"\nTimestamp: {health['timestamp']}")
                print("="*60 + "\n")

            elif choice == "17":
                logger.info("Generating learning report...")
                days = input("Number of days to analyze (default 7): ").strip()
                days = int(days) if days.isdigit() else 7

                report = await orchestrator.generate_learning_report(days=days)
                print("\n" + "="*60)
                print(f"LEARNING REPORT (Last {days} Days)")
                print("="*60)
                print(report)
                print("="*60 + "\n")

            elif choice == "18":
                logger.info("Starting scheduler...")

                phase = input("Which phase to run? (1, 2, 3, or 4, default: 4): ").strip()
                phase = int(phase) if phase.isdigit() else 4

                scheduler = ContentCreatorScheduler(phase=phase)
                scheduler.start()

                # Run initial pipeline
                if phase >= 4:
                    logger.info("Running initial Phase 4 pipeline...")
                    await orchestrator.run_full_pipeline_phase4()
                elif phase >= 3:
                    logger.info("Running initial Phase 3 pipeline...")
                    await orchestrator.run_full_pipeline_phase3()
                elif phase >= 2:
                    logger.info("Running initial Phase 2 pipeline...")
                    await orchestrator.run_full_pipeline_phase2()
                else:
                    logger.info("Running initial full pipeline...")
                    await orchestrator.run_full_pipeline()

                # Keep running
                logger.info("\nScheduler running. Press Ctrl+C to stop and return to menu.")
                try:
                    while True:
                        await asyncio.sleep(60)
                except KeyboardInterrupt:
                    logger.info("\nStopping scheduler...")
                    scheduler.stop()
                    logger.info("Scheduler stopped. Returning to menu.")

            elif choice == "19":
                logger.info("Fetching pending approvals...")
                approvals = await orchestrator.get_pending_approvals()

                if not approvals:
                    logger.info("No content awaiting approval")
                else:
                    logger.info(f"\nFound {len(approvals)} content pieces awaiting approval:\n")

                    for i, approval in enumerate(approvals, 1):
                        logger.info(f"\n{i}. Plan ID: {approval['id']}")
                        logger.info(f"   Asset: {approval['asset']}")
                        logger.info(f"   Type: {approval['type']}")
                        logger.info(f"   Confidence: {approval['confidence']:.0%}")
                        logger.info(f"   Platform: {approval['platform']}")
                        logger.info(f"   Format: {approval['format']}")
                        logger.info(f"   Preview: {approval['content_preview']}...")

                    # Ask if user wants to approve any
                    approve = input("\nEnter plan ID to approve (or 'skip'): ")

                    if approve.isdigit():
                        plan_id = int(approve)
                        success = await orchestrator.approve_content(plan_id)
                        if success:
                            logger.info(f"Content {plan_id} approved and published!")
                        else:
                            logger.error(f"Failed to publish content {plan_id}")

            elif choice == "20":
                logger.info("Exiting...")
                if scheduler:
                    scheduler.stop()
                break

            else:
                logger.warning("Invalid choice. Please enter 1-20.")

        except Exception as e:
            logger.error(f"Error: {e}")
            logger.exception("Full traceback:")

        input("\nPress Enter to continue...")


async def run_scheduled_mode():
    """Run the system in scheduled mode (daemon)."""
    setup_logger()
    print_banner()

    logger.info("Starting in scheduled mode...")
    scheduler = ContentCreatorScheduler()
    scheduler.start()

    # Run initial pipeline
    logger.info("Running initial full pipeline...")
    await scheduler.orchestrator.run_full_pipeline()

    # Keep running
    try:
        logger.info("\nScheduler is running. Press Ctrl+C to exit.")
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("\nShutting down...")
        scheduler.stop()


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--scheduled":
        asyncio.run(run_scheduled_mode())
    else:
        asyncio.run(run_interactive_mode())


if __name__ == "__main__":
    main()
