"""Telegram API integration with zero-dependency HTTP fallback."""

import json
import urllib.request
from typing import Optional

from loguru import logger

try:
    from telegram import Bot
    from telegram.error import TelegramError
except ImportError:
    Bot = None
    TelegramError = Exception


class TelegramAPI:
    """
    Telegram Bot API client for posting content to channels.
    """

    def __init__(self, bot_token: str, channel_id: str):
        """
        Initialize the Telegram API client.

        Args:
            bot_token: Telegram bot token
            channel_id: Telegram channel ID (e.g., @channelname or -100123456789)
        """
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.bot = Bot(token=bot_token) if Bot and bot_token and not bot_token.startswith("test") else None
        logger.info("Telegram API initialized")

    async def send_message(
        self, text: str, parse_mode: str = "HTML", disable_preview: bool = False
    ) -> Optional[dict]:
        """
        Send a message to the configured Telegram channel.

        Args:
            text: Message text
            parse_mode: Formatting mode (Markdown or HTML)
            disable_preview: Whether to disable link previews

        Returns:
            Dictionary with message data or None if failed
        """
        if not self.bot_token or self.bot_token.startswith("test"):
            logger.info(f"[SIMULATED TELEGRAM MESSAGE] -> {text[:80]}...")
            return {"message_id": 99999, "chat_id": self.channel_id, "text": text}

        if self.bot:
            try:
                message = await self.bot.send_message(
                    chat_id=self.channel_id,
                    text=text,
                    parse_mode=parse_mode,
                    disable_web_page_preview=disable_preview,
                )
                logger.info(f"Telegram message sent: {message.message_id}")
                return {
                    "message_id": message.message_id,
                    "chat_id": message.chat_id,
                    "text": text,
                    "date": message.date,
                }
            except Exception as e:
                logger.warning(f"Bot library failed, falling back to direct HTTP: {e}")

        # Direct HTTP Fallback
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.channel_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": disable_preview,
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                result = res_data.get("result", {})
                logger.info(f"Telegram message sent via HTTP: {result.get('message_id')}")
                return {
                    "message_id": result.get("message_id"),
                    "chat_id": self.channel_id,
                    "text": text,
                }
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return None

    async def send_photo(
        self, photo_url: str, caption: str = "", parse_mode: str = "Markdown"
    ) -> Optional[dict]:
        """
        Send a photo to the configured Telegram channel.

        Args:
            photo_url: URL of the photo
            caption: Photo caption
            parse_mode: Formatting mode

        Returns:
            Dictionary with message data or None if failed
        """
        try:
            message = await self.bot.send_photo(
                chat_id=self.channel_id, photo=photo_url, caption=caption, parse_mode=parse_mode
            )

            logger.info(f"Telegram photo sent: {message.message_id}")

            return {
                "message_id": message.message_id,
                "chat_id": message.chat_id,
                "caption": caption,
                "date": message.date,
            }

        except TelegramError as e:
            logger.error(f"Failed to send Telegram photo: {e}")
            return None

    async def edit_message(
        self, message_id: int, new_text: str, parse_mode: str = "Markdown"
    ) -> Optional[dict]:
        """
        Edit an existing message.

        Args:
            message_id: ID of the message to edit
            new_text: New message text
            parse_mode: Formatting mode

        Returns:
            Dictionary with updated message data or None if failed
        """
        try:
            message = await self.bot.edit_message_text(
                chat_id=self.channel_id, message_id=message_id, text=new_text, parse_mode=parse_mode
            )

            logger.info(f"Telegram message edited: {message_id}")

            return {"message_id": message.message_id, "text": new_text}

        except TelegramError as e:
            logger.error(f"Failed to edit Telegram message: {e}")
            return None
