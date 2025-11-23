"""OnboardingAgent - Welcomes and onboards new paying members."""

from typing import Dict, List
from datetime import datetime, timedelta

from src.agents.base_agent import BaseAgent
from src.database.connection import get_db
from src.database.models import CommunityUser, Subscription, UserTier
from src.api_integrations.discord_api import DiscordAPI
from src.api_integrations.telegram_api import TelegramAPI
from config.config import settings


class OnboardingAgent(BaseAgent):
    """
    The Onboarding Agent welcomes and onboards new members.

    Responsibilities:
    - Welcome new paying members
    - Assign appropriate roles in Discord
    - Send onboarding materials
    - Provide tour of exclusive channels
    - Track onboarding completion
    """

    def __init__(self):
        """Initialize the OnboardingAgent."""
        super().__init__("OnboardingAgent")

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

        # Tier to role mapping
        self.tier_roles = {
            UserTier.BASIC: settings.discord_role_id_basic,
            UserTier.PREMIUM: settings.discord_role_id_premium,
            UserTier.VIP: settings.discord_role_id_vip
        }

    async def execute(self) -> Dict:
        """
        Execute the onboarding process for new members.

        Returns:
            Dictionary with onboarding results
        """
        self.log_info("Starting onboarding process...")

        results = {
            "new_members_found": 0,
            "members_onboarded": 0,
            "discord_roles_assigned": 0,
            "welcome_messages_sent": 0,
            "errors": []
        }

        try:
            # Find new members who haven't been onboarded yet
            new_members = await self._get_new_members()
            results["new_members_found"] = len(new_members)

            if not new_members:
                self.log_info("No new members to onboard")
                return results

            # Onboard each new member
            for member in new_members:
                try:
                    success = await self._onboard_member(member)

                    if success:
                        results["members_onboarded"] += 1

                        if member.discord_id:
                            results["discord_roles_assigned"] += 1

                        results["welcome_messages_sent"] += 1

                except Exception as e:
                    error_msg = f"Error onboarding member {member.id}: {e}"
                    self.log_error(error_msg)
                    results["errors"].append(error_msg)

            self.log_info(
                f"Onboarding complete: {results['members_onboarded']} members onboarded"
            )

        except Exception as e:
            self.log_error(f"Onboarding execution error: {e}")
            raise

        return results

    async def _get_new_members(self) -> List[CommunityUser]:
        """
        Get members who recently subscribed but haven't been onboarded.

        Returns:
            List of CommunityUser objects
        """
        # Consider members "new" if converted in last 24 hours
        cutoff = datetime.utcnow() - timedelta(hours=24)

        with get_db() as db:
            new_members = db.query(CommunityUser).join(Subscription).filter(
                CommunityUser.tier != UserTier.FREE,
                CommunityUser.converted_at >= cutoff,
                CommunityUser.subscription_status == "active"
            ).all()

            # Filter out members who were already onboarded
            # (would track this with an 'onboarded_at' field in production)

            return new_members

    async def _onboard_member(self, member: CommunityUser) -> bool:
        """
        Onboard a new member.

        Args:
            member: CommunityUser object

        Returns:
            True if onboarding successful
        """
        self.log_info(f"Onboarding member: {member.email or member.twitter_username}")

        # Step 1: Assign Discord role if they're on Discord
        if self.discord_api and member.discord_id:
            role_id = self.tier_roles.get(member.tier)

            if role_id:
                await self.discord_api.add_role_to_member(
                    member_id=member.discord_id,
                    role_id=role_id
                )

                self.log_info(f"Discord role assigned to {member.discord_username}")

        # Step 2: Send welcome message to Discord
        if self.discord_api and member.discord_id:
            await self._send_discord_welcome(member)

        # Step 3: Send welcome to Telegram (if configured)
        if self.telegram_api and member.telegram_id:
            await self._send_telegram_welcome(member)

        # Step 4: Mark as onboarded (would add onboarded_at field in production)
        # For now, just log it
        self.log_info(f"Member {member.id} successfully onboarded")

        return True

    async def _send_discord_welcome(self, member: CommunityUser):
        """
        Send welcome message to Discord.

        Args:
            member: CommunityUser object
        """
        if not self.discord_api:
            return

        # Create personalized welcome embed
        embed = await self.discord_api.create_welcome_embed(
            member_name=member.discord_username or "Member",
            tier=member.tier.value
        )

        # Get welcome channel ID (would be in settings)
        welcome_channel_id = "your_welcome_channel_id"  # Configure in settings

        await self.discord_api.send_message(
            channel_id=welcome_channel_id,
            content=f"Welcome <@{member.discord_id}>!",
            embed=embed
        )

        self.log_info(f"Discord welcome sent to {member.discord_username}")

    async def _send_telegram_welcome(self, member: CommunityUser):
        """
        Send welcome message to Telegram.

        Args:
            member: CommunityUser object
        """
        if not self.telegram_api:
            return

        welcome_message = self._generate_telegram_welcome(member)

        await self.telegram_api.send_message(
            text=welcome_message,
            parse_mode="Markdown"
        )

        self.log_info(f"Telegram welcome sent to {member.telegram_username}")

    def _generate_telegram_welcome(self, member: CommunityUser) -> str:
        """
        Generate Telegram welcome message.

        Args:
            member: CommunityUser object

        Returns:
            Welcome message text
        """
        tier_benefits = {
            UserTier.BASIC: [
                "Daily market insights",
                "Trading signals",
                "Community chat access"
            ],
            UserTier.PREMIUM: [
                "Everything in Basic",
                "Early access to alpha signals",
                "Weekly market reports",
                "Priority support"
            ],
            UserTier.VIP: [
                "Everything in Premium",
                "1-on-1 strategy calls",
                "Exclusive VIP-only signals",
                "Direct access to analysts"
            ]
        }

        benefits = tier_benefits.get(member.tier, [])

        message = f"""
🎉 **Welcome to the {member.tier.value.upper()} Community!**

Hey {member.telegram_username or member.twitter_username or "there"}! 👋

Thank you for joining our exclusive community. You now have access to:

"""

        for benefit in benefits:
            message += f"✅ {benefit}\n"

        message += """
**Getting Started:**
1. Check pinned messages for today's insights
2. Introduce yourself in the community chat
3. Read our trading guidelines

**Need help?** Just ask in the support channel!

Let's make some alpha together! 🚀

_Automated by Content Creator AI_
"""

        return message

    async def handle_subscription_upgrade(
        self,
        user_id: int,
        old_tier: UserTier,
        new_tier: UserTier
    ):
        """
        Handle when a user upgrades their subscription.

        Args:
            user_id: CommunityUser ID
            old_tier: Previous tier
            new_tier: New tier
        """
        with get_db() as db:
            user = db.query(CommunityUser).filter(
                CommunityUser.id == user_id
            ).first()

            if not user:
                return

            # Update Discord roles
            if self.discord_api and user.discord_id:
                # Remove old role
                old_role_id = self.tier_roles.get(old_tier)
                new_role_id = self.tier_roles.get(new_tier)

                if old_role_id:
                    await self.discord_api.remove_role_from_member(
                        member_id=user.discord_id,
                        role_id=old_role_id
                    )

                if new_role_id:
                    await self.discord_api.add_role_to_member(
                        member_id=user.discord_id,
                        role_id=new_role_id
                    )

            # Send upgrade congrats message
            if self.discord_api:
                # Would send to a channel
                self.log_info(
                    f"User {user.id} upgraded from {old_tier.value} to {new_tier.value}"
                )

    async def handle_subscription_cancellation(self, user_id: int):
        """
        Handle when a user cancels their subscription.

        Args:
            user_id: CommunityUser ID
        """
        with get_db() as db:
            user = db.query(CommunityUser).filter(
                CommunityUser.id == user_id
            ).first()

            if not user:
                return

            # Remove Discord roles
            if self.discord_api and user.discord_id:
                role_id = self.tier_roles.get(user.tier)

                if role_id:
                    await self.discord_api.remove_role_from_member(
                        member_id=user.discord_id,
                        role_id=role_id
                    )

            # Update user tier
            user.tier = UserTier.FREE
            user.subscription_status = "cancelled"

            db.commit()

            self.log_info(f"User {user.id} subscription cancelled, access revoked")

    async def send_onboarding_materials(self, member: CommunityUser):
        """
        Send onboarding materials and guides to new member.

        Args:
            member: CommunityUser object
        """
        # In production, this would send:
        # - PDF guides
        # - Video tutorials
        # - Quick start checklist
        # - Community guidelines

        materials = {
            "guides": [
                "Getting Started with Crypto Trading",
                "How to Read Our Signals",
                "Risk Management Basics"
            ],
            "resources": [
                "Community Guidelines",
                "FAQ",
                "Support Channels"
            ]
        }

        self.log_info(
            f"Onboarding materials prepared for {member.id}: {materials}"
        )

        # Would actually send these via Discord/Telegram/Email
