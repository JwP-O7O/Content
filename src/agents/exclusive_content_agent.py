"""ExclusiveContentAgent - Publishes exclusive content for paying members."""

from datetime import datetime, timedelta, timezone

from config.config import settings
from src.agents.base_agent import BaseAgent
from src.api_integrations.discord_api import DiscordAPI
from src.api_integrations.telegram_api import TelegramAPI
from src.database.connection import get_db
from src.database.models import ExclusiveContent, Insight, UserTier


class ExclusiveContentAgent(BaseAgent):
    """
    The Exclusive Content Agent publishes high-alpha content for paying members.

    Responsibilities:
    - Identify high-confidence insights (>0.90 confidence)
    - Publish exclusive content to private channels
    - Tier-gate content (Basic, Premium, VIP)
    - Track engagement from paying members
    - Ensure exclusive content remains exclusive
    """

    def __init__(self):
        """Initialize the ExclusiveContentAgent."""
        super().__init__("ExclusiveContentAgent")

        # Initialize Discord
        try:
            self.discord_api = DiscordAPI(
                bot_token=settings.discord_bot_token,
                guild_id=settings.discord_guild_id
            )
        except Exception as e:
            self.log_warning(f"Discord API not configured: {e}")
            self.discord_api = None

        # Initialize Telegram
        try:
            self.telegram_api = TelegramAPI(
                bot_token=settings.telegram_bot_token,
                channel_id=settings.telegram_channel_id
            )
        except Exception as e:
            self.log_warning(f"Telegram API not configured: {e}")
            self.telegram_api = None

        # Confidence thresholds for different tiers
        self.tier_thresholds = {
            UserTier.BASIC: 0.85,      # Good insights
            UserTier.PREMIUM: 0.90,    # High-confidence insights
            UserTier.VIP: 0.95         # Ultra high-confidence alpha
        }

        # Channel IDs for different tiers (should be in settings)
        self.tier_channels = {
            UserTier.BASIC: {
                "discord": "basic_signals_channel_id",
                "telegram": "basic_telegram_channel_id"
            },
            UserTier.PREMIUM: {
                "discord": "premium_signals_channel_id",
                "telegram": "premium_telegram_channel_id"
            },
            UserTier.VIP: {
                "discord": "vip_alpha_channel_id",
                "telegram": "vip_telegram_channel_id"
            }
        }

    async def execute(self) -> dict:
        """
        Execute exclusive content publishing.

        Returns:
            Dictionary with publishing results
        """
        self.log_info("Starting exclusive content publishing...")

        results = {
            "insights_evaluated": 0,
            "content_published": 0,
            "basic_tier": 0,
            "premium_tier": 0,
            "vip_tier": 0,
            "errors": []
        }

        try:
            # Get high-confidence unpublished insights
            insights = await self._get_exclusive_insights()
            results["insights_evaluated"] = len(insights)

            if not insights:
                self.log_info("No exclusive insights to publish")
                return results

            # Publish to appropriate tiers
            for insight in insights:
                try:
                    tier = self._determine_tier_for_insight(insight)

                    if tier:
                        success = await self._publish_exclusive_content(insight, tier)

                        if success:
                            results["content_published"] += 1

                            if tier == UserTier.BASIC:
                                results["basic_tier"] += 1
                            elif tier == UserTier.PREMIUM:
                                results["premium_tier"] += 1
                            elif tier == UserTier.VIP:
                                results["vip_tier"] += 1

                except Exception as e:
                    error_msg = f"Error publishing insight {insight.id}: {e}"
                    self.log_error(error_msg)
                    results["errors"].append(error_msg)

            self.log_info(
                f"Exclusive content publishing complete: "
                f"{results['content_published']} insights published"
            )

        except Exception as e:
            self.log_error(f"Exclusive content execution error: {e}")
            raise

        return results

    async def _get_exclusive_insights(self) -> list[Insight]:
        """
        Get insights that should be published as exclusive content.

        Returns:
            List of Insight objects
        """
        with get_db() as db:
            # Get high-confidence insights from last 24 hours
            cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=24)

            insights = db.query(Insight).filter(
                Insight.is_published.is_(False),  # Not yet published publicly
                Insight.is_exclusive.is_(False),  # Not yet marked as exclusive
                Insight.confidence >= self.tier_thresholds[UserTier.BASIC],
                Insight.timestamp >= cutoff
            ).order_by(
                Insight.confidence.desc()
            ).all()

            return insights

    def _determine_tier_for_insight(self, insight: Insight) -> UserTier:
        """
        Determine which membership tier should get this insight.

        Args:
            insight: Insight object

        Returns:
            UserTier or None
        """
        # VIP gets ultra high-confidence
        if insight.confidence >= self.tier_thresholds[UserTier.VIP]:
            return UserTier.VIP

        # Premium gets high-confidence
        elif insight.confidence >= self.tier_thresholds[UserTier.PREMIUM]:
            return UserTier.PREMIUM

        # Basic gets good insights
        elif insight.confidence >= self.tier_thresholds[UserTier.BASIC]:
            return UserTier.BASIC

        return None

    async def _publish_exclusive_content(
        self,
        insight: Insight,
        tier: UserTier
    ) -> bool:
        """
        Publish exclusive content to the appropriate tier channels.

        Args:
            insight: Insight object
            tier: UserTier to publish to

        Returns:
            True if published successfully
        """
        self.log_info(
            f"Publishing exclusive content: {insight.asset} {insight.type.value} "
            f"(confidence: {insight.confidence:.0%}) to {tier.value.upper()} tier"
        )

        # Generate exclusive content text
        content_text = self._generate_exclusive_content(insight, tier)

        # Publish to Discord
        discord_published = False

        if self.discord_api:
            channel_id = self.tier_channels[tier]["discord"]

            result = await self.discord_api.send_message(
                channel_id=channel_id,
                content=content_text
            )

            if result:
                discord_published = True

                # Save to database
                await self._save_exclusive_content(
                    insight=insight,
                    tier=tier,
                    content_text=content_text,
                    platform="discord",
                    channel_id=channel_id,
                    message_id=result["id"]
                )

        # Publish to Telegram
        telegram_published = False

        if self.telegram_api:
            result = await self.telegram_api.send_message(
                text=content_text,
                parse_mode="Markdown"
            )

            if result:
                telegram_published = True

                # Save to database
                await self._save_exclusive_content(
                    insight=insight,
                    tier=tier,
                    content_text=content_text,
                    platform="telegram",
                    message_id=str(result["message_id"])
                )

        # Mark insight as exclusive
        with get_db() as db:
            insight.is_exclusive = True
            db.commit()

        return discord_published or telegram_published

    def _generate_exclusive_content(self, insight: Insight, tier: UserTier) -> str:
        """
        Generate exclusive content text for an insight.

        Args:
            insight: Insight object
            tier: UserTier

        Returns:
            Formatted content text
        """
        # Tier-specific prefixes
        tier_prefixes = {
            UserTier.BASIC: "🔔 SIGNAL",
            UserTier.PREMIUM: "⭐ PREMIUM ALPHA",
            UserTier.VIP: "💎 VIP EXCLUSIVE"
        }

        prefix = tier_prefixes.get(tier, "🔔")

        # Get LLM analysis from insight details
        llm_analysis = insight.details.get("llm_analysis", "")

        # Build content
        content = f"""
{prefix} | ${insight.asset}

**Type:** {insight.type.value.replace('_', ' ').title()}
**Confidence:** {insight.confidence:.0%}
**Time:** {insight.timestamp.strftime('%Y-%m-%d %H:%M UTC')}

**Analysis:**
{llm_analysis}

**Key Metrics:**
"""

        # Add specific metrics based on insight type
        if "price" in insight.details:
            content += f"• Price: ${insight.details['price']:.2f}\n"

        if "change_24h" in insight.details:
            content += f"• 24h Change: {insight.details['change_24h']:.2f}%\n"

        if "volume_ratio" in insight.details:
            content += f"• Volume: {insight.details['volume_ratio']:.2f}x average\n"

        # Add tier-specific footer
        if tier == UserTier.VIP:
            content += "\n⚡ **VIP ONLY** - Do not share outside this channel"
        elif tier == UserTier.PREMIUM:
            content += "\n⭐ **PREMIUM** - Members only"
        else:
            content += "\n🔒 **EXCLUSIVE** - Community members only"

        content += "\n\n_Automated by Content Creator AI_"

        return content

    async def _save_exclusive_content(
        self,
        insight: Insight,
        tier: UserTier,
        content_text: str,
        platform: str,
        channel_id: Optional[str] = None,
        message_id: Optional[str] = None
    ):
        """
        Save exclusive content to database for tracking.

        Args:
            insight: Insight object
            tier: UserTier
            content_text: The content text
            platform: Platform (discord/telegram)
            channel_id: Channel ID
            message_id: Message ID
        """
        with get_db() as db:
            exclusive = ExclusiveContent(
                insight_id=insight.id,
                content_text=content_text,
                platform=platform,
                min_tier_required=tier,
                channel_id=channel_id,
                message_id=message_id
            )

            db.add(exclusive)
            db.commit()

            self.log_info(f"Exclusive content saved to database (ID: {exclusive.id})")

    async def get_exclusive_content_stats(self, days: int = 7) -> dict:
        """
        Get statistics about exclusive content performance.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with stats
        """
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)

        with get_db() as db:
            content_items = db.query(ExclusiveContent).filter(
                ExclusiveContent.published_at >= cutoff
            ).all()

            stats_by_tier = {}

            for tier in [UserTier.BASIC, UserTier.PREMIUM, UserTier.VIP]:
                tier_content = [c for c in content_items if c.min_tier_required == tier]

                stats_by_tier[tier.value] = {
                    "total_posts": len(tier_content),
                    "total_views": sum(c.views or 0 for c in tier_content),
                    "total_reactions": sum(c.reactions or 0 for c in tier_content),
                    "avg_views": (
                        sum(c.views or 0 for c in tier_content) / len(tier_content)
                        if tier_content else 0
                    )
                }

            return {
                "period_days": days,
                "total_exclusive_posts": len(content_items),
                "by_tier": stats_by_tier
            }
