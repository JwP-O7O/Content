"""ContentStrategistAgent - Plans content strategy based on insights."""

from datetime import datetime, timedelta, timezone

from src.agents.base_agent import BaseAgent
from src.database.connection import get_db
from src.database.models import ContentFormat, ContentPlan, Insight, InsightType, PublishedContent
from src.utils.llm_client import llm_client


class ContentStrategistAgent(BaseAgent):
    SYSTEM_PROMPT = """
    <SYSTEM_MESSAGE>
    You are an advanced AI Content Strategist, designated as the "ContentStrategistAgent".
    Your primary objective is to dynamically formulate and optimize robust content strategies.
    </SYSTEM_MESSAGE>
    """

    def __init__(self):
        super().__init__("ContentStrategistAgent")
        self.llm = llm_client

        # Strategy parameters
        self.min_confidence_public = 0.65
        self.min_confidence_exclusive = 0.85
        self.max_posts_per_day = 8

        # Content format rules based on insight type and confidence
        self.format_rules = {
            InsightType.BREAKOUT: {
                "high_confidence": ContentFormat.THREAD,
                "medium_confidence": ContentFormat.SINGLE_TWEET,
            },
            InsightType.BREAKDOWN: {
                "high_confidence": ContentFormat.THREAD,
                "medium_confidence": ContentFormat.SINGLE_TWEET,
            },
            InsightType.NEWS_IMPACT: {
                "high_confidence": ContentFormat.THREAD,
                "medium_confidence": ContentFormat.SINGLE_TWEET,
            },
            InsightType.VOLUME_SPIKE: {
                "high_confidence": ContentFormat.SINGLE_TWEET,
                "medium_confidence": ContentFormat.SINGLE_TWEET,
            },
            InsightType.SENTIMENT_SHIFT: {
                "high_confidence": ContentFormat.SINGLE_TWEET,
                "medium_confidence": ContentFormat.TELEGRAM_MESSAGE,
            },
            InsightType.TECHNICAL_PATTERN: {
                "high_confidence": ContentFormat.THREAD,
                "medium_confidence": ContentFormat.SINGLE_TWEET,
            },
        }

        # Optimal posting times (hours in UTC)
        self.optimal_times = [6, 9, 12, 15, 18, 21]

        # Content repurposing settings
        self.enable_repurposing = True
        self.repurpose_high_performing_threshold = 0.05

    async def execute(self) -> dict:
        """
        Execute the content planning process.
        """
        self.log_info("Starting content strategy planning...")

        results = {
            "insights_reviewed": 0,
            "content_plans_created": 0,
            "exclusive_content_plans": 0,
            "skipped_insights": 0,
        }

        try:
            # Get unpublished insights
            insights = await self._get_unpublished_insights()
            results["insights_reviewed"] = len(insights)

            # Check current content volume for today
            todays_plans = await self._get_todays_content_plans()

            if len(todays_plans) >= self.max_posts_per_day:
                self.log_warning(
                    f"Daily content limit reached ({self.max_posts_per_day}). "
                    "Skipping content planning."
                )
                return results

            # Create content plans for each insight
            with get_db() as db:
                for insight in insights:
                    # Check if already planned
                    if insight.content_plans:
                        results["skipped_insights"] += 1
                        continue

                    # Determine if this should be exclusive content
                    is_exclusive = insight.confidence >= self.min_confidence_exclusive

                    # Skip low-confidence insights
                    if insight.confidence < self.min_confidence_public:
                        results["skipped_insights"] += 1
                        continue

                    # Create content plan
                    content_plan = self._create_content_plan(insight, is_exclusive)

                    if content_plan:
                        db.add(content_plan)
                        insight.is_exclusive = is_exclusive
                        results["content_plans_created"] += 1

                        if is_exclusive:
                            results["exclusive_content_plans"] += 1

                        if results["content_plans_created"] >= (
                            self.max_posts_per_day - len(todays_plans)
                        ):
                            break

                db.commit()

            self.log_info(
                f"Content planning complete: {results['content_plans_created']} plans created, "
                f"{results['exclusive_content_plans']} exclusive"
            )

        except Exception as e:
            self.log_error(f"Content planning error: {e}")
            raise

        return results

    async def _get_unpublished_insights(self) -> list[Insight]:
        """Get insights that haven't been published yet."""
        with get_db() as db:
            cutoff_time = datetime.now(tz=timezone.utc) - timedelta(hours=24)
            return (
                db.query(Insight)
                .filter(Insight.is_published.is_(False), Insight.timestamp >= cutoff_time)
                .order_by(Insight.confidence.desc())
                .all()
            )

    async def _get_todays_content_plans(self) -> list[ContentPlan]:
        """Get content plans created today."""
        with get_db() as db:
            today_start = datetime.now(tz=timezone.utc).replace(hour=0, minute=0, second=0)
            return db.query(ContentPlan).filter(ContentPlan.timestamp >= today_start).all()

    def _create_content_plan(self, insight: Insight, is_exclusive: bool) -> ContentPlan:
        """Create a content plan for an insight."""
        # Determine content format
        content_format = self._determine_format(insight)

        # Determine platform
        if is_exclusive:
            platform = "telegram_exclusive"
        elif content_format == ContentFormat.THREAD or insight.confidence >= 0.75:
            platform = "twitter"
        else:
            platform = "telegram_public"

        # Determine priority
        if insight.confidence >= 0.9:
            priority = "high"
        elif insight.confidence >= 0.75:
            priority = "medium"
        else:
            priority = "low"

        # Schedule for next optimal time
        scheduled_time = self._get_next_optimal_time()

        content_plan = ContentPlan(
            insight_id=insight.id,
            platform=platform,
            format=content_format,
            priority=priority,
            scheduled_for=scheduled_time,
            status="pending",
        )

        self.log_info(
            f"Created content plan: {insight.asset} {insight.type.value} "
            f"-> {platform} ({content_format.value}) "
            f"[confidence: {insight.confidence:.2f}]"
        )

        return content_plan

    def _determine_format(self, insight: Insight) -> ContentFormat:
        """Determine the best content format based on insight type and confidence."""
        rules = self.format_rules.get(insight.type)
        if not rules:
            return ContentFormat.SINGLE_TWEET

        if insight.confidence >= 0.8:
            return rules.get("high_confidence", ContentFormat.THREAD)
        return rules.get("medium_confidence", ContentFormat.SINGLE_TWEET)

    def _get_next_optimal_time(self) -> datetime:
        """Get the next optimal posting time."""
        now = datetime.now(tz=timezone.utc)
        current_hour = now.hour

        for hour in self.optimal_times:
            if hour > current_hour:
                return now.replace(hour=hour, minute=0, second=0)

        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=self.optimal_times[0], minute=0, second=0)

    async def optimize_strategy(self) -> dict:
        """Analyze past performance and optimize content strategy."""
        self.log_info("Optimizing content strategy based on performance...")

        with get_db() as db:
            cutoff = datetime.now(tz=timezone.utc) - timedelta(days=30)
            published = (
                db.query(PublishedContent).filter(PublishedContent.published_at >= cutoff).all()
            )

            if not published:
                return {"message": "Not enough data for optimization"}

            format_performance = {}
            for content in published:
                fmt = content.content_plan.format.value
                if fmt not in format_performance:
                    format_performance[fmt] = {
                        "count": 0,
                        "total_engagement": 0,
                        "avg_engagement": 0,
                    }

                format_performance[fmt]["count"] += 1
                format_performance[fmt]["total_engagement"] += content.engagement_rate or 0

            for fmt in format_performance:
                count = format_performance[fmt]["count"]
                if count > 0:
                    format_performance[fmt]["avg_engagement"] = (
                        format_performance[fmt]["total_engagement"] / count
                    )

            return {
                "analyzed_content": len(published),
                "format_performance": format_performance,
                "recommendations": self._generate_recommendations(format_performance),
            }

    def _generate_recommendations(self, performance: dict) -> list[str]:
        """Generate strategy recommendations based on performance data."""
        recommendations = []
        best_format = max(
            performance.items(), key=lambda x: x[1]["avg_engagement"], default=(None, None)
        )

        if best_format[0]:
            recommendations.append(
                f"Increase {best_format[0]} content - highest engagement "
                f"({best_format[1]['avg_engagement']:.2%})"
            )

        for fmt, data in performance.items():
            if data["avg_engagement"] < 0.02:
                recommendations.append(
                    f"Consider reducing {fmt} content - low engagement "
                    f"({data['avg_engagement']:.2%})"
                )

        return recommendations

    async def plan_content_repurposing(self) -> dict:
        """Identify high-performing content and create plans to repurpose it."""
        if not self.enable_repurposing:
            return {"repurposing_disabled": True}

        self.log_info("Planning content repurposing...")
        results = {"candidates_found": 0, "repurpose_plans_created": 0}

        with get_db() as db:
            cutoff = datetime.now(tz=timezone.utc) - timedelta(days=7)
            high_performers = (
                db.query(PublishedContent)
                .filter(
                    PublishedContent.published_at >= cutoff,
                    PublishedContent.engagement_rate >= self.repurpose_high_performing_threshold,
                )
                .all()
            )

            results["candidates_found"] = len(high_performers)

            for content in high_performers:
                if self._already_repurposed(content):
                    continue

                repurpose_plans = self._create_repurpose_plans(content)
                for plan_data in repurpose_plans:
                    repurpose_plan = ContentPlan(
                        insight_id=content.content_plan.insight_id,
                        platform=plan_data["platform"],
                        format=plan_data["format"],
                        prioroty="medium",
                        scheduled_for=self._get_next_optimal_time(),
                        status="pending",
                    )
                    db.add(repurpose_plan)
                    results["repurpose_plans_created"] += 1

            db.commit()

        return results

    def _already_repurposed(self, content: PublishedContent) -> bool:
        """Check if content has already been repurposed."""
        with get_db() as db:
            insight_id = content.content_plan.insight_id
            other_plans = (
                db.query(ContentPlan)
                .filter(
                    ContentPlan.insight_id == insight_id, ContentPlan.id != content.content_plan.id
                )
                .count()
            )
            return other_plans >= 2

    def _create_repurpose_plans(self, content: PublishedContent) -> list[dict]:
        """Create repurposed content plans for high performing content."""
        plans = []
        original_platform = content.platform
        original_format = content.content_plan.format

        if original_platform == "twitter" and original_format == ContentFormat.THREAD:
            plans.append(
                {
                    "platform": "blog",
                    "format": ContentFormat.BLOG_POST,
                    "reason": "Expand thread into detailed blog post",
                }
            )

        if original_platform == "twitter":
            plans.append(
                {
                    "platform": "telegram_public",
                    "format": ContentFormat.TELEGRAM_MESSAGE,
                    "reason": "Share Twitter success on Telegram",
                }
            )

        if original_platform == "blog":
            plans.append(
                {
                    "platform": "twitter",
                    "format": ContentFormat.THREAD,
                    "reason": "Condense blog into thread",
                }
            )

        return plans
