"""PublishingAgent - Publishes content to various platforms."""

from datetime import datetime, timezone
from typing import Optional

from config.config import settings
from src.agents.base_agent import BaseAgent
from src.api_integrations.telegram_api import TelegramAPI
from src.api_integrations.twitter_api import TwitterAPI
from src.database.connection import get_db
from src.database.models import ContentFormat, ContentPlan, PublishedContent


class PublishingAgent(BaseAgent):
    """
    The Publishing Agent publishes content to social platforms.

    Responsibilities:
    - Publish approved content to the right platforms
    - Track published content and metrics
    - Handle human-in-the-loop approval flow
    - Manage publishing schedule
    """

    def __init__(self):
        """Initialize the PublishingAgent."""
        super().__init__("PublishingAgent")

        # Initialize API clients
        try:
            self.twitter_api = TwitterAPI(
                api_key=settings.twitter_api_key,
                api_secret=settings.twitter_api_secret,
                access_token=settings.twitter_access_token,
                access_token_secret=settings.twitter_access_token_secret,
                bearer_token=settings.twitter_bearer_token
            )
        except Exception as e:
            self.log_warning(f"Twitter API not configured: {e}")
            self.twitter_api = None

        try:
            self.telegram_api = TelegramAPI(
                bot_token=settings.telegram_bot_token,
                channel_id=settings.telegram_channel_id
            )
        except Exception as e:
            self.log_warning(f"Telegram API not configured: {e}")
            self.telegram_api = None

        self.human_in_the_loop = settings.human_in_the_loop

    async def execute(self) -> dict:
        """
        Execute the publishing process.

        Returns:
            Dictionary with publishing results
        """
        self.log_info("Starting content publishing...")

        results = {
            "content_published": 0,
            "twitter_posts": 0,
            "telegram_posts": 0,
            "awaiting_approval": 0,
            "errors": []
        }

        try:
            # Get ready content plans
            ready_plans = await self._get_ready_plans()

            for plan in ready_plans:
                try:
                    if self.human_in_the_loop:
                        # Mark as awaiting approval
                        self._mark_awaiting_approval(plan)
                        results["awaiting_approval"] += 1
                    else:
                        # Auto-publish
                        success = await self._publish_plan(plan)

                        if success:
                            results["content_published"] += 1

                            if plan.platform == "twitter":
                                results["twitter_posts"] += 1
                            elif "telegram" in plan.platform:
                                results["telegram_posts"] += 1

                except Exception as e:
                    error_msg = f"Error publishing plan {plan.id}: {e}"
                    self.log_error(error_msg)
                    results["errors"].append(error_msg)

            if self.human_in_the_loop and results["awaiting_approval"] > 0:
                self.log_info(
                    f"{results['awaiting_approval']} content pieces "
                    "awaiting human approval"
                )
            else:
                self.log_info(
                    f"Publishing complete: {results['content_published']} "
                    "pieces published"
                )

        except Exception as e:
            self.log_error(f"Publishing error: {e}")
            raise

        return results

    async def _get_ready_plans(self) -> list[ContentPlan]:
        """
        Get content plans that are ready to publish.

        Returns:
            List of ready content plans
        """
        with get_db() as db:
            # Get plans that are ready and scheduled for now or earlier
            now = datetime.now(tz=timezone.utc)

            plans = db.query(ContentPlan).filter(
                ContentPlan.status == "ready",
                ContentPlan.scheduled_for <= now
            ).limit(10).all()

            return plans

    def _mark_awaiting_approval(self, plan: ContentPlan):
        """Mark a content plan as awaiting approval."""
        with get_db() as db:
            plan.status = "awaiting_approval"
            db.add(plan)
            db.commit()

        self.log_info(
            f"Content plan {plan.id} marked as awaiting approval. "
            f"Review and approve via approve_content({plan.id})"
        )

    async def _publish_plan(self, plan: ContentPlan) -> bool:
        """
        Publish a content plan to its target platform.

        Args:
            plan: ContentPlan to publish

        Returns:
            True if published successfully, False otherwise
        """
        self.log_info(
            f"Publishing {plan.format.value} to {plan.platform} "
            f"(insight: {plan.insight.asset} {plan.insight.type.value})"
        )

        # Get the generated content from the plan details
        # In a real implementation, this would be stored in the plan
        # For now, we'll regenerate or fetch it

        # Publish based on platform
        if plan.platform == "twitter":
            return await self._publish_to_twitter(plan)
        elif "telegram" in plan.platform:
            return await self._publish_to_telegram(plan)
        else:
            self.log_warning(f"Unknown platform: {plan.platform}")
            return False

    async def _publish_to_twitter(self, plan: ContentPlan) -> bool:
        """Publish content to Twitter."""
        if not self.twitter_api:
            self.log_error("Twitter API not available")
            return False

        try:
            # For this implementation, we need the actual content text
            # This would normally be stored with the plan
            # Let's create a placeholder for now

            if plan.format == ContentFormat.SINGLE_TWEET:
                # Publish single tweet
                tweet_text = self._get_content_text(plan)

                result = self.twitter_api.post_tweet(tweet_text)

                if result:
                    self._save_published_content(
                        plan=plan,
                        content_text=tweet_text,
                        post_url=result["url"],
                        post_id=result["id"]
                    )
                    return True

            elif plan.format == ContentFormat.THREAD:
                # Publish thread
                thread_tweets = self._get_thread_tweets(plan)

                result = self.twitter_api.post_thread(thread_tweets)

                if result:
                    self._save_published_content(
                        plan=plan,
                        content_text="\n\n".join(thread_tweets),
                        post_url=result[0]["url"],
                        post_id=result[0]["id"]
                    )
                    return True

            return False

        except Exception as e:
            self.log_error(f"Error publishing to Twitter: {e}")
            return False

    async def _publish_to_telegram(self, plan: ContentPlan) -> bool:
        """Publish content to Telegram."""
        if not self.telegram_api:
            self.log_error("Telegram API not available")
            return False

        try:
            message_text = self._get_content_text(plan)

            result = await self.telegram_api.send_message(message_text)

            if result:
                self._save_published_content(
                    plan=plan,
                    content_text=message_text,
                    post_id=str(result["message_id"])
                )
                return True

            return False

        except Exception as e:
            self.log_error(f"Error publishing to Telegram: {e}")
            return False

    def _get_content_text(self, plan: ContentPlan) -> str:
        """
        Get the content text for a plan.

        In a real implementation, this would be stored in the plan.
        For now, we'll create a simple placeholder.
        """
        insight = plan.insight

        # Simple template
        template = (
            f"${insight.asset} Alert\n\n"
            f"Detected: {insight.type.value}\n"
            f"Confidence: {insight.confidence:.0%}\n\n"
            f"Analysis: {insight.details.get('llm_analysis', 'Analyzing market data...')}\n\n"
            f"#crypto #{insight.asset}"
        )

        return template

    def _get_thread_tweets(self, plan: ContentPlan) -> list[str]:
        """
        Get thread tweets for a plan.

        In a real implementation, this would be stored in the plan.
        """
        insight = plan.insight

        tweets = [
            f"${insight.asset} {insight.type.value.upper()} detected "
            f"(confidence: {insight.confidence:.0%}) 🚨",

            f"Analysis: {insight.details.get('llm_analysis', 'Market data analysis...')}",

            f"Key metrics:\n"
            f"• Confidence: {insight.confidence:.0%}\n"
            f"• Type: {insight.type.value}",

            f"This is based on our proprietary analysis. "
            f"Always DYOR! #crypto #{insight.asset}"
        ]

        return tweets

    def _save_published_content(
        self,
        plan: ContentPlan,
        content_text: str,
        post_url: Optional[str] = None,
        post_id: Optional[str] = None
    ):
        """Save published content to the database."""
        with get_db() as db:
            published = PublishedContent(
                content_plan_id=plan.id,
                platform=plan.platform,
                content_text=content_text,
                post_url=post_url,
                post_id=post_id
            )

            db.add(published)

            # Update plan status
            plan.status = "published"
            plan.insight.is_published = True

            db.commit()

        self.log_info(f"Saved published content for plan {plan.id}")

    async def approve_and_publish(self, plan_id: int) -> bool:
        """
        Approve and publish a content plan (for human-in-the-loop).

        Args:
            plan_id: ID of the content plan to approve

        Returns:
            True if published successfully
        """
        with get_db() as db:
            plan = db.query(ContentPlan).filter(
                ContentPlan.id == plan_id
            ).first()

            if not plan:
                self.log_error(f"Content plan {plan_id} not found")
                return False

            if plan.status != "awaiting_approval":
                self.log_warning(
                    f"Content plan {plan_id} is not awaiting approval "
                    f"(status: {plan.status})"
                )
                return False

            # Change status to ready
            plan.status = "ready"
            db.commit()

        # Publish the plan
        return await self._publish_plan(plan)

    async def reject_content(self, plan_id: int):
        """
        Reject a content plan.

        Args:
            plan_id: ID of the content plan to reject
        """
        with get_db() as db:
            plan = db.query(ContentPlan).filter(
                ContentPlan.id == plan_id
            ).first()

            if plan:
                plan.status = "rejected"
                db.commit()
                self.log_info(f"Content plan {plan_id} rejected")

    async def get_pending_approvals(self) -> list[dict]:
        """
        Get all content plans awaiting approval.

        Returns:
            List of content plans awaiting approval
        """
        with get_db() as db:
            plans = db.query(ContentPlan).filter(
                ContentPlan.status == "awaiting_approval"
            ).all()

            return [
                {
                    "id": p.id,
                    "asset": p.insight.asset,
                    "type": p.insight.type.value,
                    "confidence": p.insight.confidence,
                    "platform": p.platform,
                    "format": p.format.value,
                    "content_preview": self._get_content_text(p)[:200]
                }
                for p in plans
            ]
