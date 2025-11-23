"""ContentStrategistAgent - Plans content strategy based on insights."""

from typing import Dict, List
from datetime import datetime, timedelta

from src.agents.base_agent import BaseAgent
from src.database.connection import get_db
from src.database.models import (
    Insight, ContentPlan, ContentFormat,
    InsightType, PublishedContent
)


class ContentStrategistAgent(BaseAgent):
    """
    The Content Strategist Agent plans the content strategy.

    Responsibilities:
    - Review insights from AnalysisAgent
    - Decide which insights to publish
    - Determine the best content format and platform
    - Schedule content for optimal posting times
    - Identify content for paid vs free channels
    """

    def __init__(self):
        """Initialize the ContentStrategistAgent."""
        super().__init__("ContentStrategistAgent")

        # Strategy parameters
        self.min_confidence_public = 0.65  # Min confidence for public content
        self.min_confidence_exclusive = 0.85  # Min confidence for paid content
        self.max_posts_per_day = 8  # Maximum content pieces per day

        # Content format rules based on insight type and confidence
        self.format_rules = {
            InsightType.BREAKOUT: {
                "high_confidence": ContentFormat.THREAD,  # >= 0.8
                "medium_confidence": ContentFormat.SINGLE_TWEET  # < 0.8
            },
            InsightType.BREAKDOWN: {
                "high_confidence": ContentFormat.THREAD,
                "medium_confidence": ContentFormat.SINGLE_TWEET
            },
            InsightType.NEWS_IMPACT: {
                "high_confidence": ContentFormat.THREAD,
                "medium_confidence": ContentFormat.SINGLE_TWEET
            },
            InsightType.VOLUME_SPIKE: {
                "high_confidence": ContentFormat.SINGLE_TWEET,
                "medium_confidence": ContentFormat.SINGLE_TWEET
            },
            InsightType.SENTIMENT_SHIFT: {
                "high_confidence": ContentFormat.SINGLE_TWEET,
                "medium_confidence": ContentFormat.TELEGRAM_MESSAGE
            },
            InsightType.TECHNICAL_PATTERN: {
                "high_confidence": ContentFormat.THREAD,
                "medium_confidence": ContentFormat.SINGLE_TWEET
            }
        }

        # Optimal posting times (hours in UTC)
        self.optimal_times = [6, 9, 12, 15, 18, 21]  # Every 3 hours

        # Content repurposing settings
        self.enable_repurposing = True
        self.repurpose_high_performing_threshold = 0.05  # 5% engagement rate

    async def execute(self) -> Dict:
        """
        Execute the content planning process.

        Returns:
            Dictionary with planning results
        """
        self.log_info("Starting content strategy planning...")

        results = {
            "insights_reviewed": 0,
            "content_plans_created": 0,
            "exclusive_content_plans": 0,
            "skipped_insights": 0
        }

        try:
            # Query and process everything within same session
            from sqlalchemy.orm import joinedload

            with get_db() as db:
                # Get unpublished insights with content_plans eagerly loaded
                cutoff_time = datetime.utcnow() - timedelta(hours=24)

                insights = db.query(Insight).options(
                    joinedload(Insight.content_plans)
                ).filter(
                    Insight.is_published == False,
                    Insight.timestamp >= cutoff_time
                ).order_by(
                    Insight.confidence.desc()
                ).all()

                results["insights_reviewed"] = len(insights)

                # Check current content volume for today
                today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
                todays_plans = db.query(ContentPlan).filter(
                    ContentPlan.timestamp >= today_start
                ).all()

                if len(todays_plans) >= self.max_posts_per_day:
                    self.log_warning(
                        f"Daily content limit reached ({self.max_posts_per_day}). "
                        "Skipping content planning."
                    )
                    return results

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

                        # Check if we've hit the daily limit
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

    async def _get_unpublished_insights(self) -> List[Insight]:
        """
        Get insights that haven't been published yet.

        Returns:
            List of unpublished insights, ordered by confidence
        """
        from sqlalchemy.orm import joinedload

        with get_db() as db:
            # Get insights from the last 24 hours that aren't published
            cutoff_time = datetime.utcnow() - timedelta(hours=24)

            insights = db.query(Insight).options(
                joinedload(Insight.content_plans)
            ).filter(
                Insight.is_published == False,
                Insight.timestamp >= cutoff_time
            ).order_by(
                Insight.confidence.desc()
            ).all()

            # Expunge objects from session so they can be used outside
            for insight in insights:
                db.expunge(insight)

            return insights

    async def _get_todays_content_plans(self) -> List[ContentPlan]:
        """
        Get content plans created today.

        Returns:
            List of today's content plans
        """
        with get_db() as db:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)

            plans = db.query(ContentPlan).filter(
                ContentPlan.timestamp >= today_start
            ).all()

            return plans

    def _create_content_plan(
        self,
        insight: Insight,
        is_exclusive: bool
    ) -> ContentPlan:
        """
        Create a content plan for an insight.

        Args:
            insight: The insight to create content for
            is_exclusive: Whether this is exclusive content

        Returns:
            ContentPlan object
        """
        # Determine content format
        content_format = self._determine_format(insight)

        # Determine platform
        if is_exclusive:
            platform = "telegram_exclusive"  # Private Telegram channel
        else:
            # Public platforms - prefer Twitter for high confidence
            if content_format == ContentFormat.THREAD or insight.confidence >= 0.75:
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
            status="pending"
        )

        self.log_info(
            f"Created content plan: {insight.asset} {insight.type.value} "
            f"-> {platform} ({content_format.value}) "
            f"[confidence: {insight.confidence:.2f}]"
        )

        return content_plan

    def _determine_format(self, insight: Insight) -> ContentFormat:
        """
        Determine the best content format for an insight.

        Args:
            insight: The insight to determine format for

        Returns:
            ContentFormat enum value
        """
        # Get format rules for this insight type
        rules = self.format_rules.get(insight.type)

        if not rules:
            return ContentFormat.SINGLE_TWEET

        # Determine confidence level
        if insight.confidence >= 0.8:
            return rules.get("high_confidence", ContentFormat.THREAD)
        else:
            return rules.get("medium_confidence", ContentFormat.SINGLE_TWEET)

    def _get_next_optimal_time(self) -> datetime:
        """
        Get the next optimal posting time.

        Returns:
            Datetime for next optimal posting
        """
        now = datetime.utcnow()
        current_hour = now.hour

        # Find next optimal time
        for hour in self.optimal_times:
            if hour > current_hour:
                next_time = now.replace(hour=hour, minute=0, second=0)
                return next_time

        # If no time found today, use first time tomorrow
        tomorrow = now + timedelta(days=1)
        next_time = tomorrow.replace(
            hour=self.optimal_times[0],
            minute=0,
            second=0
        )
        return next_time

    async def optimize_strategy(self) -> Dict:
        """
        Analyze past performance and optimize content strategy.

        Returns:
            Dictionary with optimization results
        """
        self.log_info("Optimizing content strategy based on performance...")

        with get_db() as db:
            # Get published content from last 30 days
            cutoff = datetime.utcnow() - timedelta(days=30)

            published = db.query(PublishedContent).filter(
                PublishedContent.published_at >= cutoff
            ).all()

            if not published:
                return {"message": "Not enough data for optimization"}

            # Calculate average engagement by format
            format_performance = {}

            for content in published:
                fmt = content.content_plan.format.value

                if fmt not in format_performance:
                    format_performance[fmt] = {
                        "count": 0,
                        "total_engagement": 0,
                        "avg_engagement": 0
                    }

                format_performance[fmt]["count"] += 1
                format_performance[fmt]["total_engagement"] += (
                    content.engagement_rate or 0
                )

            # Calculate averages
            for fmt in format_performance:
                count = format_performance[fmt]["count"]
                if count > 0:
                    format_performance[fmt]["avg_engagement"] = (
                        format_performance[fmt]["total_engagement"] / count
                    )

            self.log_info(f"Format performance: {format_performance}")

            return {
                "analyzed_content": len(published),
                "format_performance": format_performance,
                "recommendations": self._generate_recommendations(format_performance)
            }

    def _generate_recommendations(self, performance: Dict) -> List[str]:
        """Generate strategy recommendations based on performance data."""
        recommendations = []

        # Find best performing format
        best_format = max(
            performance.items(),
            key=lambda x: x[1]["avg_engagement"],
            default=(None, None)
        )

        if best_format[0]:
            recommendations.append(
                f"Increase {best_format[0]} content - highest engagement "
                f"({best_format[1]['avg_engagement']:.2%})"
            )

        # Find underperforming formats
        for fmt, data in performance.items():
            if data["avg_engagement"] < 0.02:  # Less than 2% engagement
                recommendations.append(
                    f"Consider reducing {fmt} content - low engagement "
                    f"({data['avg_engagement']:.2%})"
                )

        return recommendations

    async def plan_content_repurposing(self) -> Dict:
        """
        Identify high-performing content and create plans to repurpose it.

        Returns:
            Dictionary with repurposing results
        """
        if not self.enable_repurposing:
            return {"repurposing_disabled": True}

        self.log_info("Planning content repurposing...")

        results = {
            "candidates_found": 0,
            "repurpose_plans_created": 0,
            "platforms_targeted": []
        }

        with get_db() as db:
            # Find high-performing content from last 7 days
            cutoff = datetime.utcnow() - timedelta(days=7)

            high_performers = db.query(PublishedContent).filter(
                PublishedContent.published_at >= cutoff,
                PublishedContent.engagement_rate >= self.repurpose_high_performing_threshold
            ).all()

            results["candidates_found"] = len(high_performers)

            for content in high_performers:
                # Check if already repurposed
                if self._already_repurposed(content):
                    continue

                # Determine repurposing strategy
                repurpose_plans = self._create_repurpose_plans(content)

                for plan_data in repurpose_plans:
                    # Create new content plan
                    repurpose_plan = ContentPlan(
                        insight_id=content.content_plan.insight_id,
                        platform=plan_data["platform"],
                        format=plan_data["format"],
                        priority="medium",
                        scheduled_for=self._get_next_optimal_time(),
                        status="pending"
                    )

                    db.add(repurpose_plan)
                    results["repurpose_plans_created"] += 1

                    if plan_data["platform"] not in results["platforms_targeted"]:
                        results["platforms_targeted"].append(plan_data["platform"])

            db.commit()

        self.log_info(
            f"Repurposing planned: {results['repurpose_plans_created']} "
            f"plans for {len(results['platforms_targeted'])} platforms"
        )

        return results

    def _already_repurposed(self, content: PublishedContent) -> bool:
        """Check if content has already been repurposed."""
        with get_db() as db:
            # Check if there are other content plans for the same insight
            # on different platforms
            insight_id = content.content_plan.insight_id

            other_plans = db.query(ContentPlan).filter(
                ContentPlan.insight_id == insight_id,
                ContentPlan.id != content.content_plan.id
            ).count()

            # If there are already 2+ plans for this insight, skip
            return other_plans >= 2

    def _create_repurpose_plans(self, content: PublishedContent) -> List[Dict]:
        """
        Create repurposing plans for high-performing content.

        Args:
            content: Published content to repurpose

        Returns:
            List of repurpose plan specifications
        """
        plans = []
        original_platform = content.platform
        original_format = content.content_plan.format

        # Twitter thread -> Blog post
        if original_platform == "twitter" and original_format == ContentFormat.THREAD:
            plans.append({
                "platform": "blog",
                "format": ContentFormat.BLOG_POST,
                "reason": "Expand thread into detailed blog post"
            })

        # Twitter post -> Telegram
        if original_platform == "twitter":
            plans.append({
                "platform": "telegram_public",
                "format": ContentFormat.TELEGRAM_MESSAGE,
                "reason": "Share Twitter success on Telegram"
            })

        # Blog post -> Twitter thread
        if original_platform == "blog":
            plans.append({
                "platform": "twitter",
                "format": ContentFormat.THREAD,
                "reason": "Condense blog into thread"
            })

        return plans
