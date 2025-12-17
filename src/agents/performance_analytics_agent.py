"""PerformanceAnalyticsAgent - Advanced analytics and performance tracking."""

import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from anthropic import Anthropic
from sqlalchemy.orm import joinedload
from sqlalchemy import func

from config.config import settings
from src.agents.base_agent import BaseAgent
from src.database.connection import get_db
from src.database.models import (
    PerformanceSnapshot, PublishedContent, Insight,
    CommunityUser, Subscription, UserTier, ConversionAttempt,
    InsightType, ContentFormat, ContentPlan
    CommunityUser,
    ConversionAttempt,
    Insight,
    PerformanceSnapshot,
    PublishedContent,
    Subscription,
    UserTier,
)


class PerformanceAnalyticsAgent(BaseAgent):
    """
    The Performance Analytics Agent provides advanced analytics and insights.

    Responsibilities:
    - Create periodic performance snapshots
    - Track trends over time (daily, weekly, monthly)
    - Identify performance anomalies
    - Generate predictive insights
    - Calculate ROI and efficiency metrics
    - Provide executive summary reports
    """

    def __init__(self):
        """Initialize the PerformanceAnalyticsAgent."""
        super().__init__("PerformanceAnalyticsAgent")

        # Initialize LLM for insights
        self.llm_client = Anthropic(api_key=settings.anthropic_api_key)

    async def execute(self) -> dict:
        """
        Execute performance analytics workflow.

        Returns:
            Dictionary with analytics results
        """
        self.log_info("Starting performance analytics...")

        results = {
            "snapshots_created": 0,
            "trends_analyzed": 0,
            "anomalies_detected": 0,
            "predictions_generated": 0,
        }

        try:
            # Create daily snapshot
            snapshot = await self._create_performance_snapshot("daily")
            if snapshot:
                results["snapshots_created"] = 1

            # Analyze trends
            trends = await self._analyze_trends()
            results["trends_analyzed"] = len(trends)

            # Detect anomalies
            anomalies = await self._detect_anomalies()
            results["anomalies_detected"] = len(anomalies)

            # Generate predictions
            predictions = await self._generate_predictions()
            results["predictions_generated"] = len(predictions)

            self.log_info(
                f"Performance analytics complete: {results['snapshots_created']} snapshots, "
                f"{results['trends_analyzed']} trends, {results['anomalies_detected']} anomalies"
            )

        except Exception as e:
            self.log_error(f"Performance analytics error: {e}")
            raise

        return results

    async def _create_performance_snapshot(
        self, period_type: str = "daily"
    ) -> Optional[PerformanceSnapshot]:
        """
        Create a performance snapshot for the specified period.

        Args:
            period_type: Type of period (daily, weekly, monthly)

        Returns:
            Created PerformanceSnapshot or None
        """
        self.log_info(f"Creating {period_type} performance snapshot...")

        # Determine time range
        now = datetime.now(tz=timezone.utc)
        if period_type == "daily":
            cutoff = now - timedelta(days=1)
        elif period_type == "weekly":
            cutoff = now - timedelta(weeks=1)
        else:  # monthly
            cutoff = now - timedelta(days=30)

        with get_db() as db:
            # Check if snapshot already exists for today
            existing = (
                db.query(PerformanceSnapshot)
                .filter(
                    PerformanceSnapshot.snapshot_date >= cutoff,
                    PerformanceSnapshot.period_type == period_type,
                )
                .first()
            )

            if existing:
                self.log_info(f"{period_type.capitalize()} snapshot already exists")
                return existing

            # Gather content metrics with eager loading to avoid N+1 queries
            content_items = db.query(PublishedContent).options(
                joinedload(PublishedContent.content_plan).joinedload(ContentPlan.insight)
            ).filter(
                PublishedContent.published_at >= cutoff
            ).all()

            content_count = len(content_items)
            
            # Use SQL aggregations instead of Python loops for better performance
            metrics = db.query(
                func.sum(PublishedContent.views).label('total_views'),
                func.sum(
                    func.coalesce(PublishedContent.likes, 0) + 
                    func.coalesce(PublishedContent.comments, 0) + 
                    func.coalesce(PublishedContent.shares, 0)
                ).label('total_clicks'),
                func.avg(PublishedContent.engagement_rate).label('avg_engagement')
            ).filter(
                PublishedContent.published_at >= cutoff
            ).first()
            
            total_impressions = int(metrics.total_views or 0)
            total_clicks = int(metrics.total_clicks or 0)
            avg_engagement = float(metrics.avg_engagement or 0)

            # Find best performing format using SQL aggregation
            format_stats = db.query(
                ContentPlan.format,
                func.avg(PublishedContent.engagement_rate).label('avg_engagement')
            ).join(
                PublishedContent.content_plan
            ).filter(
                PublishedContent.published_at >= cutoff
            ).group_by(
                ContentPlan.format
            ).order_by(
                func.avg(PublishedContent.engagement_rate).desc()
            ).first()
            
            top_format = format_stats.format.value if format_stats else None

            # Find best performing asset using SQL aggregation
            asset_stats = db.query(
                Insight.asset,
                func.avg(PublishedContent.engagement_rate).label('avg_engagement')
            ).join(
                ContentPlan, ContentPlan.insight_id == Insight.id
            ).join(
                PublishedContent, PublishedContent.content_plan_id == ContentPlan.id
            ).filter(
                PublishedContent.published_at >= cutoff
            ).group_by(
                Insight.asset
            ).order_by(
                func.avg(PublishedContent.engagement_rate).desc()
            ).first()
            
            top_asset = asset_stats.asset if asset_stats else None

            # Find best performing insight type using SQL aggregation
            insight_stats = db.query(
                Insight.type,
                func.avg(PublishedContent.engagement_rate).label('avg_engagement')
            ).join(
                ContentPlan, ContentPlan.insight_id == Insight.id
            ).join(
                PublishedContent, PublishedContent.content_plan_id == ContentPlan.id
            ).filter(
                PublishedContent.published_at >= cutoff
            ).group_by(
                Insight.type
            ).order_by(
                func.avg(PublishedContent.engagement_rate).desc()
            ).first()
            
            top_insight_type = insight_stats.type.value if insight_stats else None
            # Gather content metrics
            content_items = (
                db.query(PublishedContent).filter(PublishedContent.published_at >= cutoff).all()
            )

            content_count = len(content_items)
            total_impressions = sum(c.views or 0 for c in content_items)
            total_clicks = sum(
                (c.likes or 0) + (c.comments or 0) + (c.shares or 0) for c in content_items
            )

            avg_engagement = 0
            if content_items:
                engagement_rates = [c.engagement_rate or 0 for c in content_items]
                avg_engagement = sum(engagement_rates) / len(engagement_rates)

            # Find best performing format
            format_performance = {}
            for content in content_items:
                fmt = content.content_plan.format.value
                if fmt not in format_performance:
                    format_performance[fmt] = []
                format_performance[fmt].append(content.engagement_rate or 0)

            top_format = None
            if format_performance:
                top_format = max(format_performance.items(), key=lambda x: sum(x[1]) / len(x[1]))[0]

            # Find best performing asset
            asset_performance = {}
            for content in content_items:
                if content.content_plan and content.content_plan.insight:
                    asset = content.content_plan.insight.asset
                    if asset not in asset_performance:
                        asset_performance[asset] = []
                    asset_performance[asset].append(content.engagement_rate or 0)

            top_asset = None
            if asset_performance:
                top_asset = max(asset_performance.items(), key=lambda x: sum(x[1]) / len(x[1]))[0]

            # Find best performing insight type
            insight_performance = {}
            for content in content_items:
                if content.content_plan and content.content_plan.insight:
                    itype = content.content_plan.insight.type.value
                    if itype not in insight_performance:
                        insight_performance[itype] = []
                    insight_performance[itype].append(content.engagement_rate or 0)

            top_insight_type = None
            if insight_performance:
                top_insight_type = max(
                    insight_performance.items(), key=lambda x: sum(x[1]) / len(x[1])
                )[0]

            # Gather audience metrics (would integrate with Twitter API in production)
            new_followers = 0  # Placeholder
            total_followers = 0  # Placeholder
            follower_growth_rate = 0.0

            # Gather monetization metrics
            new_conversions = (
                db.query(CommunityUser)
                .filter(CommunityUser.converted_at >= cutoff, CommunityUser.tier != UserTier.FREE)
                .count()
            )

            total_paying = (
                db.query(CommunityUser).filter(CommunityUser.tier != UserTier.FREE).count()
            )

            total_users = db.query(CommunityUser).count()

            conversion_rate = (new_conversions / total_users) if total_users > 0 else 0

            # Calculate revenue (approximate)
            subscriptions = db.query(Subscription).filter(Subscription.status == "active").all()

            revenue = sum(s.amount for s in subscriptions)

            # Calculate insight accuracy
            insights = db.query(Insight).filter(Insight.timestamp >= cutoff).all()

            avg_confidence = 0
            if insights:
                avg_confidence = sum(i.confidence for i in insights) / len(insights)

            # Create snapshot
            snapshot = PerformanceSnapshot(
                snapshot_date=now,
                period_type=period_type,
                content_published_count=content_count,
                avg_engagement_rate=avg_engagement,
                total_impressions=total_impressions,
                total_clicks=total_clicks,
                new_followers=new_followers,
                total_followers=total_followers,
                follower_growth_rate=follower_growth_rate,
                new_conversions=new_conversions,
                total_paying_members=total_paying,
                revenue=revenue,
                conversion_rate=conversion_rate,
                top_performing_format=top_format,
                top_performing_asset=top_asset,
                top_performing_insight_type=top_insight_type,
                avg_insight_confidence=avg_confidence,
                insight_accuracy_rate=0.0,  # Would calculate based on performance tracking
            )

            db.add(snapshot)
            db.commit()

            self.log_info(
                f"Performance snapshot created: {content_count} content, "
                f"{avg_engagement:.2%} avg engagement, ${revenue:.2f} revenue"
            )

            return snapshot

    async def _analyze_trends(self) -> list[dict]:
        """
        Analyze performance trends over time.

        Returns:
            List of trend insights
        """
        self.log_info("Analyzing performance trends...")

        trends = []

        with get_db() as db:
            # Get last 30 days of snapshots
            cutoff = datetime.now(tz=timezone.utc) - timedelta(days=30)

            snapshots = (
                db.query(PerformanceSnapshot)
                .filter(
                    PerformanceSnapshot.snapshot_date >= cutoff,
                    PerformanceSnapshot.period_type == "daily",
                )
                .order_by(PerformanceSnapshot.snapshot_date.asc())
                .all()
            )

            if len(snapshots) < 7:
                self.log_info("Not enough data for trend analysis")
                return trends

            # Analyze engagement rate trend
            engagement_trend = self._calculate_trend([s.avg_engagement_rate for s in snapshots])

            if engagement_trend:
                trends.append(
                    {
                        "metric": "engagement_rate",
                        "direction": engagement_trend["direction"],
                        "change_percentage": engagement_trend["change_pct"],
                        "significance": engagement_trend["significance"],
                    }
                )

            # Analyze conversion rate trend
            conversion_trend = self._calculate_trend([s.conversion_rate for s in snapshots])

            if conversion_trend:
                trends.append(
                    {
                        "metric": "conversion_rate",
                        "direction": conversion_trend["direction"],
                        "change_percentage": conversion_trend["change_pct"],
                        "significance": conversion_trend["significance"],
                    }
                )

            # Analyze revenue trend
            revenue_trend = self._calculate_trend([s.revenue for s in snapshots])

            if revenue_trend:
                trends.append(
                    {
                        "metric": "revenue",
                        "direction": revenue_trend["direction"],
                        "change_percentage": revenue_trend["change_pct"],
                        "significance": revenue_trend["significance"],
                    }
                )

            self.log_info(f"Identified {len(trends)} significant trends")

            return trends

    def _calculate_trend(self, values: list[float]) -> Optional[dict]:
        """
        Calculate trend direction and significance.

        Args:
            values: List of values over time

        Returns:
            Trend information or None
        """
        if len(values) < 2:
            return None

        # Simple linear regression
        n = len(values)
        x_values = list(range(n))

        # Calculate means
        mean_x = sum(x_values) / n
        mean_y = sum(values) / n

        # Calculate slope
        numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, values))
        denominator = sum((x - mean_x) ** 2 for x in x_values)

        if denominator == 0:
            return None

        slope = numerator / denominator

        # Calculate change percentage
        change_pct = (values[-1] - values[0]) / abs(values[0]) * 100 if values[0] != 0 else 0

        # Determine direction and significance
        if abs(change_pct) < 5:
            return None  # Not significant

        direction = "increasing" if slope > 0 else "decreasing"
        significance = "high" if abs(change_pct) > 20 else "medium"

        return {"direction": direction, "change_pct": change_pct, "significance": significance}

    async def _detect_anomalies(self) -> list[dict]:
        """
        Detect performance anomalies.

        Returns:
            List of detected anomalies
        """
        self.log_info("Detecting performance anomalies...")

        anomalies = []

        with get_db() as db:
            # Get last 14 days
            cutoff = datetime.now(tz=timezone.utc) - timedelta(days=14)

            snapshots = (
                db.query(PerformanceSnapshot)
                .filter(
                    PerformanceSnapshot.snapshot_date >= cutoff,
                    PerformanceSnapshot.period_type == "daily",
                )
                .order_by(PerformanceSnapshot.snapshot_date.desc())
                .all()
            )

            if len(snapshots) < 7:
                return anomalies

            # Check for engagement anomalies
            engagement_rates = [s.avg_engagement_rate for s in snapshots]
            if engagement_rates:
                anomaly = self._detect_anomaly(engagement_rates, "engagement_rate")
                if anomaly:
                    anomalies.append(anomaly)

            # Check for conversion anomalies
            conversion_rates = [s.conversion_rate for s in snapshots]
            if conversion_rates:
                anomaly = self._detect_anomaly(conversion_rates, "conversion_rate")
                if anomaly:
                    anomalies.append(anomaly)

            self.log_info(f"Detected {len(anomalies)} anomalies")

            return anomalies

    def _detect_anomaly(self, values: list[float], metric: str) -> Optional[dict]:
        """
        Detect anomaly using simple statistical method.

        Args:
            values: List of values
            metric: Metric name

        Returns:
            Anomaly information or None
        """
        if len(values) < 3:
            return None

        # Calculate mean and std dev (excluding most recent)
        historical = values[1:]
        mean = sum(historical) / len(historical)

        variance = sum((x - mean) ** 2 for x in historical) / len(historical)
        std_dev = variance**0.5

        if std_dev == 0:
            return None

        # Check if most recent value is an outlier (>2 std devs)
        current = values[0]
        z_score = abs((current - mean) / std_dev)

        if z_score > 2:
            direction = "spike" if current > mean else "drop"
            severity = "critical" if z_score > 3 else "warning"

            return {
                "metric": metric,
                "direction": direction,
                "severity": severity,
                "current_value": current,
                "expected_value": mean,
                "deviation": z_score,
            }

        return None

    async def _generate_predictions(self) -> list[dict]:
        """
        Generate predictive insights using AI.

        Returns:
            List of predictions
        """
        self.log_info("Generating predictive insights...")

        predictions = []

        with get_db() as db:
            # Get last 30 days of data
            cutoff = datetime.now(tz=timezone.utc) - timedelta(days=30)

            snapshots = (
                db.query(PerformanceSnapshot)
                .filter(
                    PerformanceSnapshot.snapshot_date >= cutoff,
                    PerformanceSnapshot.period_type == "daily",
                )
                .order_by(PerformanceSnapshot.snapshot_date.desc())
                .limit(30)
                .all()
            )

            if len(snapshots) < 7:
                return predictions

            # Prepare data for AI
            snapshot_data = [
                {
                    "date": s.snapshot_date.strftime("%Y-%m-%d"),
                    "content_count": s.content_published_count,
                    "engagement_rate": s.avg_engagement_rate,
                    "conversions": s.new_conversions,
                    "revenue": s.revenue,
                }
                for s in snapshots[:14]  # Last 2 weeks
            ]

            try:
                prompt = f"""You are a data scientist analyzing performance metrics for a content creator business. Based on the last 14 days of data, provide 2-3 actionable predictions for the next 7 days.

Performance Data (most recent first):
{json.dumps(snapshot_data, indent=2, default=str)}

Generate predictions as JSON array:
[
  {{
    "prediction": "brief prediction statement",
    "confidence": 0.0-1.0,
    "recommendation": "actionable recommendation",
    "expected_impact": "expected impact description"
  }}
]"""

                message = self.llm_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=800,
                    messages=[{"role": "user", "content": prompt}],
                )

                response_text = message.content[0].text.strip()

                # Parse JSON
                start_idx = response_text.find("[")
                end_idx = response_text.rfind("]") + 1
                json_str = response_text[start_idx:end_idx]
                predictions = json.loads(json_str)

                self.log_info(f"Generated {len(predictions)} predictions")

            except Exception as e:
                self.log_error(f"Error generating predictions: {e}")

            return predictions

    async def generate_executive_summary(self, days: int = 7) -> str:
        """
        Generate an executive summary report using AI.

        Args:
            days: Number of days to analyze

        Returns:
            Executive summary text
        """
        self.log_info(f"Generating executive summary for last {days} days...")

        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)

        with get_db() as db:
            snapshots = (
                db.query(PerformanceSnapshot)
                .filter(
                    PerformanceSnapshot.snapshot_date >= cutoff,
                    PerformanceSnapshot.period_type == "daily",
                )
                .order_by(PerformanceSnapshot.snapshot_date.desc())
                .all()
            )

            if not snapshots:
                return "Insufficient data for executive summary."

            # Aggregate metrics
            total_content = sum(s.content_published_count for s in snapshots)
            avg_engagement = sum(s.avg_engagement_rate for s in snapshots) / len(snapshots)
            total_conversions = sum(s.new_conversions for s in snapshots)
            total_revenue = sum(s.revenue for s in snapshots)

            # Get trends
            trends = await self._analyze_trends()

            # Get anomalies
            anomalies = await self._detect_anomalies()

            # Generate summary using AI
            try:
                prompt = f"""You are a business analyst. Generate a concise executive summary report.

Period: Last {days} days
Total Content Published: {total_content}
Average Engagement Rate: {avg_engagement:.2%}
Total Conversions: {total_conversions}
Total Revenue: ${total_revenue:.2f}

Trends:
{json.dumps(trends, indent=2)}

Anomalies:
{json.dumps(anomalies, indent=2)}

Generate a 3-paragraph executive summary covering:
1. Overall performance highlights
2. Key trends and insights
3. Recommendations for next steps"""

                message = self.llm_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=600,
                    messages=[{"role": "user", "content": prompt}],
                )

                return message.content[0].text.strip()

            except Exception as e:
                self.log_error(f"Error generating executive summary: {e}")
                return f"Performance Summary ({days} days): {total_content} content published, {avg_engagement:.2%} avg engagement, {total_conversions} conversions, ${total_revenue:.2f} revenue"

    async def get_roi_metrics(self, days: int = 30) -> dict:
        """
        Calculate ROI and efficiency metrics.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with ROI metrics
        """
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)

        with get_db() as db:
            # Get revenue
            subscriptions = (
                db.query(Subscription)
                .filter(Subscription.created_at >= cutoff, Subscription.status == "active")
                .all()
            )

            revenue = sum(s.amount for s in subscriptions)

            # Estimate costs (simplified - would be more detailed in production)
            content_count = (
                db.query(PublishedContent).filter(PublishedContent.published_at >= cutoff).count()
            )

            # Rough cost estimate: API calls, server, etc.
            estimated_costs = content_count * 0.50  # $0.50 per content piece

            roi = (
                ((revenue - estimated_costs) / estimated_costs * 100) if estimated_costs > 0 else 0
            )

            # Efficiency metrics
            conversion_attempts = (
                db.query(ConversionAttempt).filter(ConversionAttempt.sent_at >= cutoff).count()
            )

            conversion_efficiency = (
                (len(subscriptions) / conversion_attempts * 100) if conversion_attempts > 0 else 0
            )

            return {
                "period_days": days,
                "total_revenue": revenue,
                "estimated_costs": estimated_costs,
                "net_profit": revenue - estimated_costs,
                "roi_percentage": roi,
                "content_produced": content_count,
                "revenue_per_content": revenue / content_count if content_count > 0 else 0,
                "conversion_attempts": conversion_attempts,
                "conversions": len(subscriptions),
                "conversion_efficiency": conversion_efficiency,
            }
