"""CommunityModeratorAgent - Moderates private community channels."""

import re
from datetime import datetime, timezone
from typing import Optional

from anthropic import Anthropic

from config.config import settings
from src.agents.base_agent import BaseAgent
from src.api_integrations.discord_api import DiscordAPI
from src.api_integrations.telegram_api import TelegramAPI
from src.database.connection import get_db
from src.database.models import ModerationAction


class CommunityModeratorAgent(BaseAgent):
    """
    The Community Moderator Agent moderates private channels.

    Responsibilities:
    - Monitor messages in private channels
    - Detect spam, scams, and inappropriate content
    - Automatically remove violating content
    - Warn, mute, kick, or ban users as needed
    - Log all moderation actions
    - Use AI to detect subtle violations
    """

    def __init__(self):
        """Initialize the CommunityModeratorAgent."""
        super().__init__("CommunityModeratorAgent")

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

        # Initialize LLM for content moderation
        self.llm_client = Anthropic(api_key=settings.anthropic_api_key)

        # Moderation rules
        self.spam_patterns = [
            r"(?i)(buy|sell|click|check\s+out).{0,50}(link|here|now)",
            r"(?i)t\.me/[\w]+",  # Telegram links
            r"(?i)discord\.gg/[\w]+",  # Discord invites
            r"(?i)(earn|make).{0,20}\$\d+",  # Money making schemes
            r"(?i)(dm|message)\s+me",  # Soliciting DMs
        ]

        self.scam_keywords = [
            "investment opportunity", "guaranteed profit", "double your",
            "airdrop", "free crypto", "send me", "100x", "moon soon",
            "pump", "rug pull", "private key", "seed phrase"
        ]

        self.offensive_keywords = [
            "scam", "fraud", "fake", "ponzi", "pyramid"
            # Add more as needed, would use better list in production
        ]

        # Confidence threshold for AI moderation
        self.ai_moderation_threshold = 0.8

    async def execute(self) -> dict:
        """
        Execute moderation checks.

        Returns:
            Dictionary with moderation results
        """
        self.log_info("Starting community moderation...")

        results = {
            "messages_checked": 0,
            "violations_detected": 0,
            "messages_deleted": 0,
            "users_warned": 0,
            "users_muted": 0,
            "users_banned": 0,
            "errors": []
        }

        try:
            # Check Discord messages
            if self.discord_api:
                discord_results = await self._moderate_discord_channels()
                results["messages_checked"] += discord_results["messages_checked"]
                results["violations_detected"] += discord_results["violations"]
                results["messages_deleted"] += discord_results["deleted"]
                results["users_warned"] += discord_results["warned"]

            self.log_info(
                f"Moderation complete: {results['violations_detected']} violations detected, "
                f"{results['messages_deleted']} messages deleted"
            )

        except Exception as e:
            self.log_error(f"Moderation execution error: {e}")
            raise

        return results

    async def _moderate_discord_channels(self) -> dict:
        """
        Moderate Discord channels.

        Returns:
            Dictionary with moderation results
        """
        results = {
            "messages_checked": 0,
            "violations": 0,
            "deleted": 0,
            "warned": 0
        }

        if not self.discord_api:
            return results

        # Get channels to moderate (would be configured)
        channels_to_moderate = [
            "general_chat_channel_id",
            "trading_signals_channel_id"
        ]

        for channel_id in channels_to_moderate:
            try:
                # Get recent messages
                messages = await self.discord_api.get_channel_messages(
                    channel_id=channel_id,
                    limit=50
                )

                results["messages_checked"] += len(messages)

                # Check each message
                for message in messages:
                    violation = await self._check_message_for_violations(
                        message["content"],
                        message["author_id"],
                        message["author_name"]
                    )

                    if violation:
                        results["violations"] += 1

                        # Take action
                        action_taken = await self._take_moderation_action(
                            platform="discord",
                            user_id=message["author_id"],
                            user_name=message["author_name"],
                            message_content=message["content"],
                            violation_type=violation["type"],
                            confidence=violation["confidence"],
                            channel_id=channel_id,
                            message_id=message["id"]
                        )

                        if action_taken == "deleted":
                            results["deleted"] += 1
                        elif action_taken == "warned":
                            results["warned"] += 1

            except Exception as e:
                self.log_error(f"Error moderating channel {channel_id}: {e}")

        return results

    async def _check_message_for_violations(
        self,
        content: str,
        user_id: str,
        user_name: str
    ) -> Optional[dict]:
        """
        Check a message for violations.

        Args:
            content: Message content
            user_id: User ID
            user_name: Username

        Returns:
            Violation details or None
        """
        # Check for spam patterns
        for pattern in self.spam_patterns:
            if re.search(pattern, content):
                return {
                    "type": "spam",
                    "confidence": 0.95,
                    "reason": "Matches spam pattern"
                }

        # Check for scam keywords
        content_lower = content.lower()

        for keyword in self.scam_keywords:
            if keyword in content_lower:
                return {
                    "type": "scam",
                    "confidence": 0.85,
                    "reason": f"Contains scam keyword: {keyword}"
                }

        # Check for offensive content
        for keyword in self.offensive_keywords:
            if keyword in content_lower:
                # Use AI to verify context
                is_violation = await self._ai_moderation_check(content, "offensive")

                if is_violation:
                    return {
                        "type": "offensive",
                        "confidence": 0.75,
                        "reason": "Offensive language detected"
                    }

        # Use AI for advanced moderation
        ai_violation = await self._ai_comprehensive_check(content)

        if ai_violation:
            return ai_violation

        return None

    async def _ai_moderation_check(
        self,
        content: str,
        violation_type: str
    ) -> bool:
        """
        Use AI to check if content is actually a violation.

        Args:
            content: Message content
            violation_type: Type of potential violation

        Returns:
            True if it's a violation
        """
        try:
            prompt = f"""You are a content moderator. Determine if this message violates community guidelines for "{violation_type}" content.

Message: "{content}"

Is this a violation? Consider context and intent.

Respond with just "YES" or "NO"."""

            message = self.llm_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=10,
                messages=[{"role": "user", "content": prompt}]
            )

            response = message.content[0].text.strip().upper()

            return response == "YES"

        except Exception as e:
            self.log_error(f"AI moderation check error: {e}")
            return False

    async def _ai_comprehensive_check(self, content: str) -> Optional[dict]:
        """
        Use AI for comprehensive moderation check.

        Args:
            content: Message content

        Returns:
            Violation details or None
        """
        try:
            prompt = f"""You are an expert content moderator for a crypto trading community. Analyze this message for violations:

Message: "{content}"

Check for:
1. Scams or fraudulent schemes
2. Spam or unsolicited promotion
3. Personal attacks or harassment
4. Misleading information
5. Soliciting private information

If you detect a violation, respond with JSON:
{{"violation": true, "type": "scam/spam/harassment/misleading", "confidence": 0.0-1.0, "reason": "brief explanation"}}

If no violation:
{{"violation": false}}"""

            message = self.llm_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text.strip()

            # Parse JSON response
            import json

            try:
                result = json.loads(response_text)

                if result.get("violation") and result.get("confidence", 0) >= self.ai_moderation_threshold:
                    return {
                        "type": result["type"],
                        "confidence": result["confidence"],
                        "reason": result["reason"]
                    }

            except json.JSONDecodeError:
                self.log_warning(f"Failed to parse AI response: {response_text}")

        except Exception as e:
            self.log_error(f"AI comprehensive check error: {e}")

        return None

    async def _take_moderation_action(
        self,
        platform: str,
        user_id: str,
        user_name: str,
        message_content: str,
        violation_type: str,
        confidence: float,
        channel_id: str,
        message_id: str
    ) -> str:
        """
        Take appropriate moderation action.

        Args:
            platform: Platform (discord/telegram)
            user_id: User ID
            user_name: Username
            message_content: The violating message
            violation_type: Type of violation
            confidence: Confidence score
            channel_id: Channel ID
            message_id: Message ID

        Returns:
            Action taken (deleted, warned, muted, banned)
        """
        action = "none"

        # Determine severity
        if violation_type in ["scam", "spam"] and confidence >= 0.9:
            # High confidence scam/spam - delete immediately and warn
            if platform == "discord" and self.discord_api:
                await self.discord_api.delete_message(channel_id, message_id)
                action = "deleted"

        elif violation_type == "offensive" and confidence >= 0.8:
            # Offensive content - delete and warn
            if platform == "discord" and self.discord_api:
                await self.discord_api.delete_message(channel_id, message_id)
                action = "warned"

        # Log the moderation action
        await self._log_moderation_action(
            user_id=user_id,
            platform_user_id=user_id,
            action_type=action,
            reason=f"{violation_type} (confidence: {confidence:.0%})",
            platform=platform,
            message_content=message_content,
            channel_id=channel_id,
            automated=True,
            agent_confidence=confidence
        )

        self.log_info(
            f"Moderation action: {action} - User: {user_name}, "
            f"Type: {violation_type}, Confidence: {confidence:.0%}"
        )

        return action

    async def _log_moderation_action(
        self,
        user_id: Optional[int],
        platform_user_id: str,
        action_type: str,
        reason: str,
        platform: str,
        message_content: str,
        channel_id: str,
        automated: bool,
        agent_confidence: float
    ):
        """
        Log moderation action to database.

        Args:
            user_id: CommunityUser ID (if known)
            platform_user_id: Platform-specific user ID
            action_type: Type of action taken
            reason: Reason for action
            platform: Platform (discord/telegram)
            message_content: The message content
            channel_id: Channel ID
            automated: Whether action was automated
            agent_confidence: AI confidence score
        """
        with get_db() as db:
            moderation = ModerationAction(
                user_id=user_id,
                platform_user_id=platform_user_id,
                action_type=action_type,
                reason=reason,
                platform=platform,
                message_content=message_content,
                channel_id=channel_id,
                automated=automated,
                agent_confidence=agent_confidence
            )

            db.add(moderation)
            db.commit()

    async def get_moderation_stats(self, days: int = 7) -> dict:
        """
        Get moderation statistics.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with moderation stats
        """
        from datetime import datetime, timezone

        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)

        with get_db() as db:
            actions = db.query(ModerationAction).filter(
                ModerationAction.timestamp >= cutoff
            ).all()

            stats = {
                "period_days": days,
                "total_actions": len(actions),
                "automated_actions": len([a for a in actions if a.automated]),
                "manual_actions": len([a for a in actions if not a.automated]),
                "by_type": {},
                "by_platform": {}
            }

            # Count by action type
            for action in actions:
                action_type = action.action_type

                if action_type not in stats["by_type"]:
                    stats["by_type"][action_type] = 0

                stats["by_type"][action_type] += 1

            # Count by platform
            for action in actions:
                platform = action.platform

                if platform not in stats["by_platform"]:
                    stats["by_platform"][platform] = 0

                stats["by_platform"][platform] += 1

            return stats
