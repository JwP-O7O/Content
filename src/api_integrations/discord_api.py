"""Discord API integration for private community management."""

import discord
from discord.ext import commands
from typing import Dict, List, Optional
from loguru import logger


class DiscordAPI:
    """
    Discord API client for managing private community.
    """

    def __init__(self, bot_token: str, guild_id: str):
        """
        Initialize the Discord API client.

        Args:
            bot_token: Discord bot token
            guild_id: Discord server (guild) ID
        """
        self.bot_token = bot_token
        self.guild_id = guild_id

        # Create bot instance
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        self.bot = commands.Bot(command_prefix='!', intents=intents)

        # Setup event handlers
        self._setup_handlers()

        logger.info("Discord API initialized")

    def _setup_handlers(self):
        """Setup Discord event handlers."""

        @self.bot.event
        async def on_ready():
            logger.info(f"Discord bot logged in as {self.bot.user}")

        @self.bot.event
        async def on_member_join(member):
            logger.info(f"New member joined: {member.name}")

        @self.bot.event
        async def on_message(message):
            if message.author == self.bot.user:
                return

            # Log all messages for moderation
            logger.debug(f"Message from {message.author}: {message.content}")

            await self.bot.process_commands(message)

    async def start(self):
        """Start the Discord bot."""
        try:
            await self.bot.start(self.bot_token)
        except Exception as e:
            logger.error(f"Error starting Discord bot: {e}")

    async def stop(self):
        """Stop the Discord bot."""
        await self.bot.close()

    async def send_message(
        self,
        channel_id: str,
        content: str,
        embed: Optional[discord.Embed] = None
    ) -> Optional[Dict]:
        """
        Send a message to a Discord channel.

        Args:
            channel_id: Discord channel ID
            content: Message content
            embed: Optional Discord embed

        Returns:
            Message data or None
        """
        try:
            channel = self.bot.get_channel(int(channel_id))

            if not channel:
                logger.error(f"Channel {channel_id} not found")
                return None

            message = await channel.send(content=content, embed=embed)

            logger.info(f"Discord message sent to {channel_id}: {message.id}")

            return {
                "id": str(message.id),
                "channel_id": str(message.channel.id),
                "content": message.content,
                "timestamp": message.created_at
            }

        except Exception as e:
            logger.error(f"Error sending Discord message: {e}")
            return None

    async def create_welcome_embed(self, member_name: str, tier: str) -> discord.Embed:
        """
        Create a welcome embed for new members.

        Args:
            member_name: Member's display name
            tier: Membership tier

        Returns:
            Discord embed
        """
        embed = discord.Embed(
            title=f"Welcome {member_name}! 🎉",
            description=(
                f"Thank you for joining our **{tier.upper()}** community!\n\n"
                "You now have access to exclusive crypto insights and alpha signals."
            ),
            color=discord.Color.green()
        )

        embed.add_field(
            name="📊 What You Get",
            value=(
                "• Real-time market analysis\n"
                "• Exclusive trading signals\n"
                "• Daily crypto insights\n"
                "• Priority support"
            ),
            inline=False
        )

        embed.add_field(
            name="📌 Getting Started",
            value=(
                "1. Check out <#channel-id> for today's insights\n"
                "2. Introduce yourself in <#intro-channel>\n"
                "3. Read the rules in <#rules-channel>"
            ),
            inline=False
        )

        embed.set_footer(text="Automated by Content Creator AI")

        return embed

    async def add_role_to_member(
        self,
        member_id: str,
        role_id: str
    ) -> bool:
        """
        Add a role to a Discord member.

        Args:
            member_id: Discord member ID
            role_id: Discord role ID

        Returns:
            True if successful
        """
        try:
            guild = self.bot.get_guild(int(self.guild_id))

            if not guild:
                logger.error(f"Guild {self.guild_id} not found")
                return False

            member = guild.get_member(int(member_id))
            role = guild.get_role(int(role_id))

            if not member or not role:
                logger.error(f"Member or role not found")
                return False

            await member.add_roles(role)

            logger.info(f"Role {role.name} added to {member.name}")

            return True

        except Exception as e:
            logger.error(f"Error adding role: {e}")
            return False

    async def remove_role_from_member(
        self,
        member_id: str,
        role_id: str
    ) -> bool:
        """
        Remove a role from a Discord member.

        Args:
            member_id: Discord member ID
            role_id: Discord role ID

        Returns:
            True if successful
        """
        try:
            guild = self.bot.get_guild(int(self.guild_id))
            member = guild.get_member(int(member_id))
            role = guild.get_role(int(role_id))

            if not member or not role:
                return False

            await member.remove_roles(role)

            logger.info(f"Role {role.name} removed from {member.name}")

            return True

        except Exception as e:
            logger.error(f"Error removing role: {e}")
            return False

    async def kick_member(self, member_id: str, reason: str) -> bool:
        """
        Kick a member from the Discord server.

        Args:
            member_id: Discord member ID
            reason: Reason for kick

        Returns:
            True if successful
        """
        try:
            guild = self.bot.get_guild(int(self.guild_id))
            member = guild.get_member(int(member_id))

            if not member:
                return False

            await member.kick(reason=reason)

            logger.info(f"Member {member.name} kicked: {reason}")

            return True

        except Exception as e:
            logger.error(f"Error kicking member: {e}")
            return False

    async def ban_member(
        self,
        member_id: str,
        reason: str,
        delete_message_days: int = 1
    ) -> bool:
        """
        Ban a member from the Discord server.

        Args:
            member_id: Discord member ID
            reason: Reason for ban
            delete_message_days: Days of messages to delete

        Returns:
            True if successful
        """
        try:
            guild = self.bot.get_guild(int(self.guild_id))
            member = guild.get_member(int(member_id))

            if not member:
                return False

            await member.ban(
                reason=reason,
                delete_message_days=delete_message_days
            )

            logger.info(f"Member {member.name} banned: {reason}")

            return True

        except Exception as e:
            logger.error(f"Error banning member: {e}")
            return False

    async def delete_message(self, channel_id: str, message_id: str) -> bool:
        """
        Delete a message from a channel.

        Args:
            channel_id: Discord channel ID
            message_id: Discord message ID

        Returns:
            True if successful
        """
        try:
            channel = self.bot.get_channel(int(channel_id))

            if not channel:
                return False

            message = await channel.fetch_message(int(message_id))
            await message.delete()

            logger.info(f"Message {message_id} deleted from {channel_id}")

            return True

        except Exception as e:
            logger.error(f"Error deleting message: {e}")
            return False

    async def get_channel_messages(
        self,
        channel_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get recent messages from a channel.

        Args:
            channel_id: Discord channel ID
            limit: Number of messages to fetch

        Returns:
            List of message dictionaries
        """
        try:
            channel = self.bot.get_channel(int(channel_id))

            if not channel:
                return []

            messages = []

            async for message in channel.history(limit=limit):
                messages.append({
                    "id": str(message.id),
                    "author_id": str(message.author.id),
                    "author_name": message.author.name,
                    "content": message.content,
                    "timestamp": message.created_at,
                    "attachments": [a.url for a in message.attachments]
                })

            return messages

        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return []

    def create_moderation_embed(
        self,
        action: str,
        user: str,
        reason: str,
        moderator: str = "AI Moderator"
    ) -> discord.Embed:
        """
        Create an embed for moderation actions.

        Args:
            action: Type of action (warn, kick, ban, etc.)
            user: User being moderated
            reason: Reason for action
            moderator: Who took the action

        Returns:
            Discord embed
        """
        color_map = {
            "warn": discord.Color.yellow(),
            "kick": discord.Color.orange(),
            "ban": discord.Color.red(),
            "delete": discord.Color.dark_gray()
        }

        embed = discord.Embed(
            title=f"🛡️ Moderation Action: {action.upper()}",
            description=f"**User:** {user}\n**Reason:** {reason}",
            color=color_map.get(action.lower(), discord.Color.blue()),
            timestamp=discord.utils.utcnow()
        )

        embed.set_footer(text=f"Moderator: {moderator}")

        return embed
