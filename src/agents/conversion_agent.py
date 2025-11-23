"""ConversionAgent - Converts highly engaged users to paying members."""

from datetime import datetime, timedelta, timezone

from anthropic import Anthropic

from config.config import settings
from src.agents.base_agent import BaseAgent
from src.api_integrations.stripe_api import StripeAPI
from src.api_integrations.twitter_api import TwitterAPI
from src.database.connection import get_db
from src.database.models import CommunityUser, ConversionAttempt, UserInteraction, UserTier


class ConversionAgent(BaseAgent):
    """
    The Conversion Agent identifies and converts highly engaged users.

    Responsibilities:
    - Calculate engagement scores for all users
    - Identify highly engaged free users
    - Generate personalized DMs with discount offers
    - Track conversion attempts and outcomes
    - Create payment links with discount codes
    """

    def __init__(self):
        """Initialize the ConversionAgent."""
        super().__init__("ConversionAgent")

        # Initialize APIs
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

        # Initialize Stripe
        try:
            self.stripe_api = StripeAPI(api_key=settings.stripe_api_key)
        except Exception as e:
            self.log_warning(f"Stripe API not configured: {e}")
            self.stripe_api = None

        # Initialize LLM for personalized messages
        self.llm_client = Anthropic(api_key=settings.anthropic_api_key)

        # Conversion parameters
        self.min_engagement_score = settings.conversion_min_engagement_score
        self.discount_percentage = settings.conversion_discount_percentage
        self.dm_cooldown_days = settings.conversion_dm_cooldown_days
        self.max_dms_per_run = 10

    async def execute(self) -> dict:
        """
        Execute the conversion process.

        Returns:
            Dictionary with conversion results
        """
        self.log_info("Starting user conversion process...")

        results = {
            "users_evaluated": 0,
            "high_engagement_users": 0,
            "dms_sent": 0,
            "discount_codes_created": 0,
            "errors": []
        }

        try:
            # Update engagement scores for all users
            await self._update_engagement_scores()

            # Identify conversion candidates
            candidates = await self._identify_conversion_candidates()
            results["users_evaluated"] = len(candidates)
            results["high_engagement_users"] = len(candidates)

            if not candidates:
                self.log_info("No conversion candidates found")
                return results

            # Create discount codes
            discount_code = await self._create_discount_code()

            if discount_code:
                results["discount_codes_created"] = 1

            # Send conversion DMs
            dm_count = 0

            for user in candidates[:self.max_dms_per_run]:
                try:
                    success = await self._send_conversion_dm(user, discount_code)

                    if success:
                        dm_count += 1

                except Exception as e:
                    error_msg = f"Error sending DM to user {user.id}: {e}"
                    self.log_error(error_msg)
                    results["errors"].append(error_msg)

            results["dms_sent"] = dm_count

            self.log_info(
                f"Conversion process complete: {dm_count} DMs sent to "
                f"{len(candidates)} high-engagement users"
            )

        except Exception as e:
            self.log_error(f"Conversion execution error: {e}")
            raise

        return results

    async def _update_engagement_scores(self):
        """Update engagement scores for all users based on their interactions."""
        self.log_info("Updating engagement scores...")

        with get_db() as db:
            users = db.query(CommunityUser).all()

            for user in users:
                # Get user's interactions from last 30 days
                cutoff = datetime.now(tz=timezone.utc) - timedelta(days=30)

                interactions = db.query(UserInteraction).filter(
                    UserInteraction.user_id == user.id,
                    UserInteraction.timestamp >= cutoff
                ).all()

                # Calculate weighted engagement score
                score = self._calculate_engagement_score(interactions)

                user.engagement_score = score
                user.total_interactions = len(interactions)

                if interactions:
                    user.last_interaction = max(i.timestamp for i in interactions)

            db.commit()

    def _calculate_engagement_score(self, interactions: list[UserInteraction]) -> float:
        """
        Calculate engagement score based on interactions.

        Args:
            interactions: List of user interactions

        Returns:
            Engagement score (0-100)
        """
        if not interactions:
            return 0

        # Weight different interaction types
        weights = {
            "like": 1,
            "reply": 3,
            "retweet": 2,
            "quote": 4,
            "dm_open": 5,
            "dm_click": 10
        }

        total_value = sum(
            weights.get(interaction.interaction_type, 1) * interaction.engagement_value
            for interaction in interactions
        )

        # Normalize to 0-100 scale (adjust divisor based on your data)
        score = min(100, (total_value / 50) * 100)

        return round(score, 2)

    async def _identify_conversion_candidates(self) -> list[CommunityUser]:
        """
        Identify users who are good candidates for conversion.

        Returns:
            List of CommunityUser objects
        """
        self.log_info("Identifying conversion candidates...")

        with get_db() as db:
            # Find highly engaged FREE users who haven't been DMed recently
            cooldown_cutoff = datetime.now(tz=timezone.utc) - timedelta(days=self.dm_cooldown_days)

            candidates = db.query(CommunityUser).filter(
                CommunityUser.tier == UserTier.FREE,
                CommunityUser.engagement_score >= self.min_engagement_score,
                CommunityUser.subscription_status == "inactive",
                # Either never DMed or DMed long ago
                (CommunityUser.conversion_dm_sent.is_(False)) |
                (CommunityUser.conversion_dm_sent_at < cooldown_cutoff)
            ).order_by(
                CommunityUser.engagement_score.desc()
            ).all()

            self.log_info(f"Found {len(candidates)} conversion candidates")

            return candidates

    async def _create_discount_code(self) -> dict:
        """
        Create a time-limited discount code.

        Returns:
            Discount code data or None
        """
        if not self.stripe_api:
            return None

        try:
            # Create a discount code valid for 7 days
            coupon = self.stripe_api.create_discount_code(
                percent_off=self.discount_percentage,
                duration="once",
                max_redemptions=self.max_dms_per_run
            )

            self.log_info(
                f"Created discount code: {coupon['id']} "
                f"({self.discount_percentage}% off)"
            )

            return coupon

        except Exception as e:
            self.log_error(f"Error creating discount code: {e}")
            return None

    async def _send_conversion_dm(
        self,
        user: CommunityUser,
        discount_code: dict
    ) -> bool:
        """
        Send a personalized conversion DM to a user.

        Args:
            user: CommunityUser object
            discount_code: Discount code data

        Returns:
            True if DM sent successfully
        """
        if not self.twitter_api:
            self.log_warning("Twitter API not available for DMs")
            return False

        # Generate personalized message
        message = await self._generate_conversion_message(user, discount_code)

        # Create payment link with discount
        payment_link = None

        if self.stripe_api and discount_code:
            payment_link = self.stripe_api.create_payment_link(
                price_id=settings.stripe_price_id_basic,
                metadata={
                    "user_id": user.id,
                    "twitter_id": user.twitter_id,
                    "source": "conversion_agent"
                },
                discount_code=discount_code["id"]
            )

        # Add payment link to message
        if payment_link:
            message += f"\n\n🔗 Join now: {payment_link}"

        # In practice, send actual DM via Twitter API
        # For now, we'll log it
        self.log_info(
            f"Would send conversion DM to {user.twitter_username}:\n{message}"
        )

        # Track the conversion attempt
        with get_db() as db:
            attempt = ConversionAttempt(
                user_id=user.id,
                platform="twitter",
                message_text=message,
                discount_code=discount_code["id"] if discount_code else None,
                discount_percentage=self.discount_percentage,
                status="sent"
            )

            db.add(attempt)

            # Update user
            user.conversion_dm_sent = True
            user.conversion_dm_sent_at = datetime.now(tz=timezone.utc)

            db.commit()

        return True

    async def _generate_conversion_message(
        self,
        user: CommunityUser,
        discount_code: dict
    ) -> str:
        """
        Generate a personalized conversion message using LLM.

        Args:
            user: CommunityUser object
            discount_code: Discount code data

        Returns:
            Personalized message text
        """
        try:
            prompt = f"""You are a friendly crypto community manager. Write a personalized DM to convert an engaged free user to a paid member.

User info:
- Username: {user.twitter_username or "there"}
- Engagement score: {user.engagement_score}/100 (highly engaged!)
- Total interactions: {user.total_interactions}

Offer:
- Exclusive crypto insights and alpha signals
- {self.discount_percentage}% discount (limited time)
- Access to private Discord community

Requirements:
- Personal and friendly tone (not salesy)
- Acknowledge their engagement
- Emphasize value and exclusivity
- Create urgency with the discount
- Max 280 characters (Twitter DM)

DM:"""

            message = self.llm_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )

            dm_text = message.content[0].text.strip()

            # Ensure it fits in 280 characters
            if len(dm_text) > 280:
                dm_text = dm_text[:277] + "..."

            return dm_text

        except Exception as e:
            self.log_error(f"Error generating conversion message: {e}")

            # Fallback template
            return (
                f"Hey {user.twitter_username or 'there'}! 👋 "
                f"I've noticed you're very engaged with our content "
                f"({user.total_interactions} interactions!). "
                f"We're offering {self.discount_percentage}% off our exclusive "
                f"community for engaged members like you. "
                f"Interested in getting early alpha signals?"
            )

    async def track_conversion_success(
        self,
        user_id: int,
        stripe_customer_id: str
    ):
        """
        Track when a user successfully converts to paying member.

        Args:
            user_id: CommunityUser ID
            stripe_customer_id: Stripe customer ID
        """
        with get_db() as db:
            user = db.query(CommunityUser).filter(
                CommunityUser.id == user_id
            ).first()

            if user:
                user.tier = UserTier.BASIC
                user.subscription_status = "active"
                user.converted_at = datetime.now(tz=timezone.utc)

                # Update conversion attempt status
                attempt = db.query(ConversionAttempt).filter(
                    ConversionAttempt.user_id == user_id,
                    ConversionAttempt.status == "sent"
                ).order_by(
                    ConversionAttempt.sent_at.desc()
                ).first()

                if attempt:
                    attempt.status = "converted"
                    attempt.converted_at = datetime.now(tz=timezone.utc)

                db.commit()

                self.log_info(
                    f"User {user.twitter_username} successfully converted! 🎉"
                )

    async def get_conversion_metrics(self, days: int = 30) -> dict:
        """
        Get conversion metrics for the last N days.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with conversion metrics
        """
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)

        with get_db() as db:
            attempts = db.query(ConversionAttempt).filter(
                ConversionAttempt.sent_at >= cutoff
            ).all()

            total_attempts = len(attempts)
            converted = len([a for a in attempts if a.status == "converted"])
            opened = len([a for a in attempts if a.opened_at is not None])
            clicked = len([a for a in attempts if a.clicked_at is not None])

            conversion_rate = (converted / total_attempts * 100) if total_attempts > 0 else 0
            open_rate = (opened / total_attempts * 100) if total_attempts > 0 else 0
            click_rate = (clicked / total_attempts * 100) if total_attempts > 0 else 0

            return {
                "period_days": days,
                "total_dm_attempts": total_attempts,
                "conversions": converted,
                "conversion_rate": round(conversion_rate, 2),
                "open_rate": round(open_rate, 2),
                "click_rate": round(click_rate, 2)
            }
