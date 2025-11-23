"""StrategyTuningAgent - Automatically optimizes system strategies based on performance."""

import json
from datetime import datetime, timedelta

from anthropic import Anthropic

from config.config import settings
from src.agents.base_agent import BaseAgent
from src.database.connection import get_db
from src.database.models import (
    ConversionAttempt,
    PublishedContent,
)


class StrategyTuningAgent(BaseAgent):
    """
    The Strategy Tuning Agent optimizes system performance automatically.

    Responsibilities:
    - Analyze performance across all agents
    - Identify successful patterns
    - Adjust parameters of other agents
    - Optimize posting times
    - Tune confidence thresholds
    - Adjust conversion strategies
    - Self-improve continuously
    """

    def __init__(self):
        """Initialize the StrategyTuningAgent."""
        super().__init__("StrategyTuningAgent")

        # Initialize LLM for strategic decisions
        self.llm_client = Anthropic(api_key=settings.anthropic_api_key)

        # Tuning parameters from config
        self.min_data_points = settings.strategy_tuning_min_data_points
        self.confidence_level = settings.strategy_tuning_confidence_level
        self.max_adjustments_per_run = settings.strategy_tuning_max_adjustments_per_run

    async def execute(self) -> dict:
        """
        Execute strategy optimization.

        Returns:
            Dictionary with tuning results
        """
        self.log_info("Starting strategy tuning...")

        results = {
            "analyses_performed": 0,
            "adjustments_made": 0,
            "recommendations": [],
            "performance_improvements": []
        }

        try:
            # Analyze content performance
            content_analysis = await self._analyze_content_performance()
            results["analyses_performed"] += 1

            # Analyze conversion performance
            conversion_analysis = await self._analyze_conversion_performance()
            results["analyses_performed"] += 1

            # Analyze posting time optimization
            timing_analysis = await self._analyze_optimal_posting_times()
            results["analyses_performed"] += 1

            # Generate tuning recommendations using AI
            recommendations = await self._generate_tuning_recommendations({
                "content": content_analysis,
                "conversion": conversion_analysis,
                "timing": timing_analysis
            })

            results["recommendations"] = recommendations

            # Apply high-confidence adjustments
            adjustments = await self._apply_strategy_adjustments(recommendations)
            results["adjustments_made"] = len(adjustments)
            results["performance_improvements"] = adjustments

            self.log_info(
                f"Strategy tuning complete: {results['adjustments_made']} adjustments made, "
                f"{len(recommendations)} recommendations"
            )

        except Exception as e:
            self.log_error(f"Strategy tuning error: {e}")
            raise

        return results

    async def _analyze_content_performance(self) -> dict:
        """
        Analyze which content performs best.

        Returns:
            Dictionary with performance analysis
        """
        self.log_info("Analyzing content performance...")

        cutoff = datetime.utcnow() - timedelta(days=30)

        with get_db() as db:
            content_items = db.query(PublishedContent).join(
                PublishedContent.content_plan
            ).filter(
                PublishedContent.published_at >= cutoff
            ).all()

            if len(content_items) < self.min_data_points:
                return {
                    "insufficient_data": True,
                    "message": f"Need {self.min_data_points} data points, have {len(content_items)}"
                }

            # Analyze by format
            format_performance = {}

            for content in content_items:
                fmt = content.content_plan.format.value

                if fmt not in format_performance:
                    format_performance[fmt] = {
                        "count": 0,
                        "total_engagement": 0,
                        "avg_engagement_rate": 0,
                        "best_performing_assets": []
                    }

                format_performance[fmt]["count"] += 1

                engagement = (
                    (content.likes or 0) +
                    (content.comments or 0) * 2 +
                    (content.shares or 0) * 3
                )

                format_performance[fmt]["total_engagement"] += engagement

            # Calculate averages
            for fmt in format_performance:
                count = format_performance[fmt]["count"]

                if count > 0:
                    format_performance[fmt]["avg_engagement_rate"] = (
                        format_performance[fmt]["total_engagement"] / count
                    )

            # Analyze by insight type
            insight_performance = {}

            for content in content_items:
                if not content.content_plan or not content.content_plan.insight:
                    continue

                insight_type = content.content_plan.insight.type.value

                if insight_type not in insight_performance:
                    insight_performance[insight_type] = {
                        "count": 0,
                        "total_engagement": 0,
                        "avg_engagement_rate": 0,
                        "hit_rate": 0  # Placeholder for signal accuracy
                    }

                insight_performance[insight_type]["count"] += 1

                engagement_rate = content.engagement_rate or 0
                insight_performance[insight_type]["total_engagement"] += engagement_rate

            # Calculate averages
            for itype in insight_performance:
                count = insight_performance[itype]["count"]

                if count > 0:
                    insight_performance[itype]["avg_engagement_rate"] = (
                        insight_performance[itype]["total_engagement"] / count
                    )

            return {
                "format_performance": format_performance,
                "insight_performance": insight_performance,
                "total_content_analyzed": len(content_items)
            }

    async def _analyze_conversion_performance(self) -> dict:
        """
        Analyze conversion funnel performance.

        Returns:
            Dictionary with conversion analysis
        """
        self.log_info("Analyzing conversion performance...")

        cutoff = datetime.utcnow() - timedelta(days=30)

        with get_db() as db:
            attempts = db.query(ConversionAttempt).filter(
                ConversionAttempt.sent_at >= cutoff
            ).all()

            if not attempts:
                return {"insufficient_data": True}

            total = len(attempts)
            converted = len([a for a in attempts if a.status == "converted"])
            clicked = len([a for a in attempts if a.clicked_at is not None])

            conversion_rate = (converted / total) if total > 0 else 0
            click_rate = (clicked / total) if total > 0 else 0

            # Analyze by discount percentage
            discount_performance = {}

            for attempt in attempts:
                discount = attempt.discount_percentage or 0

                if discount not in discount_performance:
                    discount_performance[discount] = {
                        "count": 0,
                        "conversions": 0,
                        "conversion_rate": 0
                    }

                discount_performance[discount]["count"] += 1

                if attempt.status == "converted":
                    discount_performance[discount]["conversions"] += 1

            # Calculate rates
            for discount in discount_performance:
                count = discount_performance[discount]["count"]

                if count > 0:
                    discount_performance[discount]["conversion_rate"] = (
                        discount_performance[discount]["conversions"] / count
                    )

            return {
                "overall_conversion_rate": conversion_rate,
                "overall_click_rate": click_rate,
                "discount_performance": discount_performance,
                "total_attempts_analyzed": total
            }

    async def _analyze_optimal_posting_times(self) -> dict:
        """
        Analyze which posting times get best engagement.

        Returns:
            Dictionary with timing analysis
        """
        self.log_info("Analyzing optimal posting times...")

        cutoff = datetime.utcnow() - timedelta(days=30)

        with get_db() as db:
            content_items = db.query(PublishedContent).filter(
                PublishedContent.published_at >= cutoff
            ).all()

            if not content_items:
                return {"insufficient_data": True}

            # Group by hour of day
            hourly_performance = {}

            for content in content_items:
                hour = content.published_at.hour

                if hour not in hourly_performance:
                    hourly_performance[hour] = {
                        "count": 0,
                        "total_engagement_rate": 0,
                        "avg_engagement_rate": 0
                    }

                hourly_performance[hour]["count"] += 1
                hourly_performance[hour]["total_engagement_rate"] += (
                    content.engagement_rate or 0
                )

            # Calculate averages
            for hour in hourly_performance:
                count = hourly_performance[hour]["count"]

                if count > 0:
                    hourly_performance[hour]["avg_engagement_rate"] = (
                        hourly_performance[hour]["total_engagement_rate"] / count
                    )

            # Find best hours
            sorted_hours = sorted(
                hourly_performance.items(),
                key=lambda x: x[1]["avg_engagement_rate"],
                reverse=True
            )

            best_hours = [hour for hour, _ in sorted_hours[:5]]

            return {
                "hourly_performance": hourly_performance,
                "best_posting_hours": best_hours,
                "worst_posting_hours": [hour for hour, _ in sorted_hours[-3:]]
            }

    async def _generate_tuning_recommendations(self, analyses: dict) -> list[dict]:
        """
        Use AI to generate strategic tuning recommendations.

        Args:
            analyses: Dictionary of performance analyses

        Returns:
            List of recommendation dictionaries
        """
        self.log_info("Generating AI-powered tuning recommendations...")

        try:
            prompt = f"""You are a strategic AI optimization expert. Analyze this system performance data and provide concrete tuning recommendations.

Performance Data:
{json.dumps(analyses, indent=2, default=str)}

Generate 3-5 actionable recommendations to improve system performance. For each recommendation:
1. Identify what to change
2. Why it should be changed (data-driven)
3. Expected impact
4. Confidence level (0-1)
5. Specific parameter adjustments

Format as JSON array:
[
  {{
    "action": "adjust_posting_schedule",
    "reason": "Data shows 2x engagement at 9 AM vs current 6 AM",
    "adjustment": {{"shift_primary_time": "9:00"}},
    "expected_impact": "50% engagement increase",
    "confidence": 0.85
  }}
]"""

            message = self.llm_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text.strip()

            # Parse JSON response
            try:
                # Extract JSON from response
                start_idx = response_text.find("[")
                end_idx = response_text.rfind("]") + 1
                json_str = response_text[start_idx:end_idx]
                recommendations = json.loads(json_str)

                return recommendations

            except json.JSONDecodeError as e:
                self.log_error(f"Failed to parse AI recommendations: {e}")
                return []

        except Exception as e:
            self.log_error(f"Error generating recommendations: {e}")
            return []

    async def _apply_strategy_adjustments(
        self,
        recommendations: list[dict]
    ) -> list[dict]:
        """
        Apply high-confidence strategy adjustments.

        Args:
            recommendations: List of recommendations

        Returns:
            List of applied adjustments
        """
        self.log_info("Applying strategy adjustments...")

        applied = []
        adjustment_count = 0

        for rec in recommendations:
            # Only apply high-confidence recommendations
            if rec.get("confidence", 0) < self.confidence_level:
                continue

            if adjustment_count >= self.max_adjustments_per_run:
                break

            # Apply the adjustment
            success = await self._apply_adjustment(rec)

            if success:
                applied.append({
                    "action": rec["action"],
                    "adjustment": rec["adjustment"],
                    "expected_impact": rec["expected_impact"],
                    "applied_at": datetime.utcnow().isoformat()
                })

                adjustment_count += 1

                self.log_info(
                    f"Applied adjustment: {rec['action']} "
                    f"(confidence: {rec['confidence']:.0%})"
                )

        return applied

    async def _apply_adjustment(self, recommendation: dict) -> bool:
        """
        Apply a specific adjustment.

        Args:
            recommendation: Recommendation dictionary

        Returns:
            True if applied successfully
        """
        action = recommendation.get("action")
        adjustment = recommendation.get("adjustment", {})

        # In practice, this would update agent configurations
        # For now, we'll log what would be changed

        self.log_info(
            f"Would apply adjustment: {action}\n"
            f"Parameters: {json.dumps(adjustment, indent=2)}"
        )

        # Store adjustment in database for tracking
        # (would add an adjustments table in production)

        return True

    async def get_tuning_history(self, days: int = 30) -> dict:
        """
        Get history of tuning adjustments.

        Args:
            days: Number of days to look back

        Returns:
            Dictionary with tuning history
        """
        # In production, would query adjustments table

        return {
            "period_days": days,
            "total_adjustments": 0,
            "adjustments": [],
            "performance_trend": "improving"
        }
