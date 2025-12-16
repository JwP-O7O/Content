"""AnalyticsAgent - Tracks and analyzes system performance."""

from datetime import datetime, timedelta, timezone

from src.agents.base_agent import BaseAgent
from src.database.connection import get_db
from src.database.models import AgentLog, ContentPlan, Insight, PublishedContent
from src.utils.metrics_collector import MetricsCollector


class AnalyticsAgent(BaseAgent):
    """
    The Analytics Agent tracks and analyzes system performance.

    Responsibilities:
    - Collect engagement metrics from all platforms
    - Generate performance reports
    - Identify trending topics and successful strategies
    - Track agent performance and efficiency
    - Provide actionable insights for optimization
    """

    def __init__(self):
        """Initialize the AnalyticsAgent."""
        super().__init__("AnalyticsAgent")
        self.metrics_collector = MetricsCollector()

    async def execute(self) -> dict:
        """
        Execute analytics collection and reporting.

        Returns:
            Dictionary with analytics results
        """
        self.log_info("Starting analytics collection...")

        results = {
            "metrics_collected": False,
            "performance_summary": {},
            "trending_topics": [],
            "agent_performance": {},
            "recommendations": [],
        }

        try:
            # Collect latest metrics
            metrics_results = await self.metrics_collector.collect_all_metrics(hours_back=48)
            results["metrics_collected"] = metrics_results["content_updated"] > 0

            # Generate performance summary
            results["performance_summary"] = await self.metrics_collector.get_performance_summary(
                days=7
            )

            # Identify trending topics
            results["trending_topics"] = await self.metrics_collector.get_trending_topics(days=7)

            # Analyze agent performance
            results["agent_performance"] = await self._analyze_agent_performance()

            # Generate recommendations
            results["recommendations"] = await self._generate_recommendations(
                results["performance_summary"], results["trending_topics"]
            )

            self.log_info("Analytics collection complete")

        except Exception as e:
            self.log_error(f"Analytics error: {e}")
            raise

        return results

    async def _analyze_agent_performance(self) -> dict:
        """
        Analyze the performance of all agents.

        Returns:
            Dictionary with agent performance metrics
        """
        self.log_info("Analyzing agent performance...")

        with get_db() as db:
            # Get agent logs from last 7 days
            cutoff = datetime.now(tz=timezone.utc) - timedelta(days=7)

            logs = db.query(AgentLog).filter(AgentLog.timestamp >= cutoff).all()

            if not logs:
                return {"message": "No agent activity logged"}

            # Aggregate by agent
            agent_stats = {}

            for log in logs:
                agent_name = log.agent_name

                if agent_name not in agent_stats:
                    agent_stats[agent_name] = {
                        "total_runs": 0,
                        "successful_runs": 0,
                        "failed_runs": 0,
                        "total_execution_time": 0,
                        "avg_execution_time": 0,
                        "success_rate": 0,
                    }

                agent_stats[agent_name]["total_runs"] += 1

                if log.status == "success":
                    agent_stats[agent_name]["successful_runs"] += 1
                elif log.status == "error":
                    agent_stats[agent_name]["failed_runs"] += 1

                if log.execution_time:
                    agent_stats[agent_name]["total_execution_time"] += log.execution_time

            # Calculate averages and rates
            for agent_name in agent_stats:
                stats = agent_stats[agent_name]
                total_runs = stats["total_runs"]

                if total_runs > 0:
                    stats["success_rate"] = stats["successful_runs"] / total_runs
                    stats["avg_execution_time"] = stats["total_execution_time"] / total_runs

            return agent_stats

    async def _generate_recommendations(self, performance: dict, trending: list[dict]) -> list[str]:
        """
        Generate actionable recommendations based on analytics.

        Args:
            performance: Performance summary
            trending: Trending topics list

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Check overall engagement
        avg_engagement = performance.get("avg_engagement_rate", 0)

        if avg_engagement < 0.02:  # Less than 2%
            recommendations.append(
                "⚠️ Low engagement detected. Consider:\n"
                "  - Adjusting posting times\n"
                "  - Improving content quality\n"
                "  - Using more visual content"
            )
        elif avg_engagement > 0.05:  # Greater than 5%
            recommendations.append("✅ Strong engagement! Continue current strategy and scale up")

        # Trending topics recommendations
        if trending:
            top_topic = trending[0]
            recommendations.append(
                f"🔥 Trending: {top_topic['asset']} {top_topic['type']} "
                f"({top_topic['avg_engagement']:.1%} engagement). "
                f"Create more content about this topic."
            )

        # Platform-specific recommendations
        platform_breakdown = performance.get("platform_breakdown", {})

        if platform_breakdown:
            best_platform = max(
                platform_breakdown.items(), key=lambda x: x[1].get("avg_engagement_rate", 0)
            )

            recommendations.append(
                f"📊 Best platform: {best_platform[0]} "
                f"({best_platform[1]['avg_engagement_rate']:.2%} avg engagement). "
                f"Increase content frequency on this platform."
            )

        # Content volume recommendations
        total_content = performance.get("total_content", 0)
        period_days = performance.get("period_days", 7)
        posts_per_day = total_content / period_days if period_days > 0 else 0

        if posts_per_day < 3:
            recommendations.append(
                f"📈 Current: {posts_per_day:.1f} posts/day. "
                "Consider increasing to 4-6 posts/day for better reach."
            )
        elif posts_per_day > 10:
            recommendations.append(
                f"⚡ High volume: {posts_per_day:.1f} posts/day. " "Monitor for audience fatigue."
            )

        return recommendations

    async def generate_report(self, days: int = 7) -> str:
        """
        Generate a comprehensive analytics report.

        Args:
            days: Number of days to include in report

        Returns:
            Formatted report string
        """
        self.log_info(f"Generating {days}-day analytics report...")

        # Collect all analytics
        analytics = await self.execute()

        # Format report
        report = f"""
╔══════════════════════════════════════════════════════════╗
║          CONTENT CREATOR - ANALYTICS REPORT              ║
║          Period: Last {days} days                            ║
║          Generated: {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}        ║
╚══════════════════════════════════════════════════════════╝

📊 PERFORMANCE SUMMARY
{'─' * 60}
"""

        perf = analytics.get("performance_summary", {})

        if "total_content" in perf:
            report += f"""
Total Content Published: {perf['total_content']}
Total Views:            {perf.get('total_views', 0):,}
Total Likes:            {perf.get('total_likes', 0):,}
Total Comments:         {perf.get('total_comments', 0):,}
Total Shares:           {perf.get('total_shares', 0):,}
Avg Engagement Rate:    {perf.get('avg_engagement_rate', 0):.2%}

"""

        # Best performing content
        if "best_performing" in perf:
            best = perf["best_performing"]
            report += f"""🏆 BEST PERFORMING CONTENT
{'─' * 60}
Platform:       {best['platform']}
Engagement:     {best['engagement_rate']:.2%}
Preview:        {best['preview']}...

"""

        # Trending topics
        trending = analytics.get("trending_topics", [])
        if trending:
            report += f"""🔥 TRENDING TOPICS
{'─' * 60}
"""
            for i, topic in enumerate(trending[:5], 1):
                report += (
                    f"{i}. {topic['asset']} - {topic['type']} ({topic['avg_engagement']:.2%})\n"
                )

            report += "\n"

        # Platform breakdown
        if "platform_breakdown" in perf:
            report += f"""📱 PLATFORM BREAKDOWN
{'─' * 60}
"""
            for platform, stats in perf["platform_breakdown"].items():
                report += f"{platform:20} {stats['count']:3} posts | {stats['avg_engagement_rate']:.2%} avg engagement\n"

            report += "\n"

        # Recommendations
        recommendations = analytics.get("recommendations", [])
        if recommendations:
            report += f"""💡 RECOMMENDATIONS
{'─' * 60}
"""
            for i, rec in enumerate(recommendations, 1):
                report += f"{i}. {rec}\n\n"

        # Agent performance
        agent_perf = analytics.get("agent_performance", {})
        if agent_perf:
            report += f"""🤖 AGENT PERFORMANCE
{'─' * 60}
"""
            for agent, stats in agent_perf.items():
                report += (
                    f"{agent:30} "
                    f"{stats['success_rate']:.1%} success | "
                    f"{stats['avg_execution_time']:.2f}s avg\n"
                )

        report += f"""
{'═' * 60}
End of Report
"""

        return report

    async def get_kpi_dashboard(self) -> dict:
        """
        Get key performance indicators for dashboard display.

        Returns:
            Dictionary with KPIs
        """
        with get_db() as db:
            now = datetime.now(tz=timezone.utc)

            # Last 24 hours
            last_24h = now - timedelta(hours=24)

            # Last 7 days
            last_7d = now - timedelta(days=7)

            # Count insights generated
            insights_24h = db.query(Insight).filter(Insight.timestamp >= last_24h).count()

            insights_7d = db.query(Insight).filter(Insight.timestamp >= last_7d).count()

            # Count content published
            published_24h = (
                db.query(PublishedContent).filter(PublishedContent.published_at >= last_24h).count()
            )

            published_7d = (
                db.query(PublishedContent).filter(PublishedContent.published_at >= last_7d).count()
            )

            # Get total engagement
            content_7d = (
                db.query(PublishedContent).filter(PublishedContent.published_at >= last_7d).all()
            )

            total_engagement = sum(
                (c.likes or 0) + (c.comments or 0) + (c.shares or 0) for c in content_7d
            )

            avg_engagement_rate = (
                sum(c.engagement_rate or 0 for c in content_7d) / len(content_7d)
                if content_7d
                else 0
            )

            # Content in pipeline
            pending_plans = (
                db.query(ContentPlan)
                .filter(ContentPlan.status.in_(["pending", "ready", "awaiting_approval"]))
                .count()
            )

            return {
                "insights_generated_24h": insights_24h,
                "insights_generated_7d": insights_7d,
                "content_published_24h": published_24h,
                "content_published_7d": published_7d,
                "total_engagement_7d": total_engagement,
                "avg_engagement_rate_7d": avg_engagement_rate,
                "content_in_pipeline": pending_plans,
                "last_updated": now.isoformat(),
            }
