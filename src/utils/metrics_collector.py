"""Metrics collection and tracking utilities."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from loguru import logger

from config.config import settings
from src.api_integrations.twitter_api import TwitterAPI
from src.database.connection import get_db
from src.database.models import PublishedContent


class MetricsCollector:
    """
    Collects and updates engagement metrics for published content.
    """

    def __init__(self):
        """Initialize the metrics collector."""
        self.twitter_api = None

        try:
            self.twitter_api = TwitterAPI(
                api_key=settings.twitter_api_key,
                api_secret=settings.twitter_api_secret,
                access_token=settings.twitter_access_token,
                access_token_secret=settings.twitter_access_token_secret,
                bearer_token=settings.twitter_bearer_token
            )
        except Exception as e:
            logger.warning(f"Twitter API not configured: {e}")

    async def collect_all_metrics(self, hours_back: int = 48) -> dict:
        """
        Collect metrics for all recent published content.

        Args:
            hours_back: How many hours back to collect metrics for

        Returns:
            Dictionary with collection results
        """
        logger.info(f"Collecting metrics for content from last {hours_back} hours...")

        results = {
            "content_updated": 0,
            "total_views": 0,
            "total_likes": 0,
            "total_engagement": 0,
            "errors": []
        }

        cutoff_time = datetime.now(tz=timezone.utc) - timedelta(hours=hours_back)

        with get_db() as db:
            content_list = db.query(PublishedContent).filter(
                PublishedContent.published_at >= cutoff_time
            ).all()

            for content in content_list:
                try:
                    metrics = await self.collect_metrics_for_content(content)

                    if metrics:
                        # Update content with new metrics
                        content.views = metrics.get("views", content.views or 0)
                        content.likes = metrics.get("likes", content.likes or 0)
                        content.comments = metrics.get("comments", content.comments or 0)
                        content.shares = metrics.get("shares", content.shares or 0)
                        content.engagement_rate = metrics.get("engagement_rate", 0)

                        results["content_updated"] += 1
                        results["total_views"] += content.views
                        results["total_likes"] += content.likes
                        results["total_engagement"] += (
                            content.likes + content.comments + content.shares
                        )

                except Exception as e:
                    error_msg = f"Error collecting metrics for {content.id}: {e}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)

            db.commit()

        logger.info(
            f"Metrics collection complete: {results['content_updated']} items updated"
        )

        return results

    async def collect_metrics_for_content(
        self,
        content: PublishedContent
    ) -> Optional[dict]:
        """
        Collect metrics for a specific piece of content.

        Args:
            content: PublishedContent object

        Returns:
            Dictionary with metrics
        """
        if content.platform == "twitter":
            return await self._collect_twitter_metrics(content)
        if "telegram" in content.platform:
            return await self._collect_telegram_metrics(content)
        return None

    async def _collect_twitter_metrics(
        self,
        content: PublishedContent
    ) -> Optional[dict]:
        """Collect metrics from Twitter."""
        if not self.twitter_api or not content.post_id:
            return None

        try:
            # Fetch tweet metrics using Twitter API
            tweet = self.twitter_api.client.get_tweet(
                content.post_id,
                tweet_fields=["public_metrics"]
            )

            if not tweet.data:
                return None

            public_metrics = tweet.data.public_metrics

            # Calculate engagement rate
            total_engagement = (
                public_metrics["like_count"] +
                public_metrics["reply_count"] +
                public_metrics["retweet_count"] +
                public_metrics["quote_count"]
            )

            # Impressions might not always be available
            impressions = public_metrics.get("impression_count", 0)

            engagement_rate = (
                total_engagement / impressions if impressions > 0 else 0
            )

            return {
                "views": impressions,
                "likes": public_metrics["like_count"],
                "comments": public_metrics["reply_count"],
                "shares": public_metrics["retweet_count"] + public_metrics["quote_count"],
                "engagement_rate": engagement_rate
            }

        except Exception as e:
            logger.error(f"Error fetching Twitter metrics: {e}")
            return None

    async def _collect_telegram_metrics(
        self,
        content: PublishedContent
    ) -> Optional[dict]:
        """Collect metrics from Telegram."""
        # Telegram doesn't provide view counts via bot API for channels
        # Would need MTProto API for detailed analytics

        # Return placeholder metrics
        return {
            "views": 0,
            "likes": 0,  # Telegram doesn't have likes
            "comments": 0,
            "shares": 0,
            "engagement_rate": 0
        }

    async def get_performance_summary(self, days: int = 7) -> dict:
        """
        Get performance summary for the last N days.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with performance summary
        """
        logger.info(f"Generating performance summary for last {days} days...")

        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)

        with get_db() as db:
            content_list = db.query(PublishedContent).filter(
                PublishedContent.published_at >= cutoff
            ).all()

            if not content_list:
                return {"message": "No content found for this period"}

            # Calculate aggregated metrics
            total_content = len(content_list)
            total_views = sum(c.views or 0 for c in content_list)
            total_likes = sum(c.likes or 0 for c in content_list)
            total_comments = sum(c.comments or 0 for c in content_list)
            total_shares = sum(c.shares or 0 for c in content_list)

            avg_engagement_rate = (
                sum(c.engagement_rate or 0 for c in content_list) / total_content
                if total_content > 0 else 0
            )

            # Find best performing content
            best_content = max(
                content_list,
                key=lambda c: c.engagement_rate or 0
            )

            # Performance by platform
            platform_stats = {}
            for content in content_list:
                platform = content.platform
                if platform not in platform_stats:
                    platform_stats[platform] = {
                        "count": 0,
                        "total_engagement": 0,
                        "avg_engagement_rate": 0
                    }

                platform_stats[platform]["count"] += 1
                platform_stats[platform]["total_engagement"] += (
                    (content.likes or 0) +
                    (content.comments or 0) +
                    (content.shares or 0)
                )

            # Calculate platform averages
            for platform in platform_stats:
                count = platform_stats[platform]["count"]
                if count > 0:
                    platform_content = [
                        c for c in content_list if c.platform == platform
                    ]
                    platform_stats[platform]["avg_engagement_rate"] = (
                        sum(c.engagement_rate or 0 for c in platform_content) / count
                    )

            return {
                "period_days": days,
                "total_content": total_content,
                "total_views": total_views,
                "total_likes": total_likes,
                "total_comments": total_comments,
                "total_shares": total_shares,
                "avg_engagement_rate": avg_engagement_rate,
                "best_performing": {
                    "id": best_content.id,
                    "platform": best_content.platform,
                    "engagement_rate": best_content.engagement_rate,
                    "preview": best_content.content_text[:100]
                },
                "platform_breakdown": platform_stats
            }

    async def get_trending_topics(self, days: int = 7) -> list[dict]:
        """
        Identify trending topics based on high-performing content.

        Args:
            days: Number of days to analyze

        Returns:
            List of trending topics
        """
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)

        with get_db() as db:
            # Get high-performing content
            high_performers = db.query(PublishedContent).filter(
                PublishedContent.published_at >= cutoff,
                PublishedContent.engagement_rate >= 0.03  # 3% threshold
            ).all()

            # Extract topics (assets) from insights
            topic_performance = {}

            for content in high_performers:
                if not content.content_plan or not content.content_plan.insight:
                    continue

                asset = content.content_plan.insight.asset
                insight_type = content.content_plan.insight.type.value

                topic_key = f"{asset}_{insight_type}"

                if topic_key not in topic_performance:
                    topic_performance[topic_key] = {
                        "asset": asset,
                        "type": insight_type,
                        "count": 0,
                        "avg_engagement": 0,
                        "total_engagement_rate": 0
                    }

                topic_performance[topic_key]["count"] += 1
                topic_performance[topic_key]["total_engagement_rate"] += (
                    content.engagement_rate or 0
                )

            # Calculate averages and sort
            trending = []
            for _topic_key, data in topic_performance.items():
                data["avg_engagement"] = (
                    data["total_engagement_rate"] / data["count"]
                )
                trending.append(data)

            # Sort by average engagement
            trending.sort(key=lambda x: x["avg_engagement"], reverse=True)

            return trending[:10]  # Top 10 trending topics
