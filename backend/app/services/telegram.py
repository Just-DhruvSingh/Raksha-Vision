import os
import logging
from typing import Optional, Dict, Any
import httpx
from dotenv import load_dotenv

# Automatically load environment variables from .env file if present
load_dotenv()

logger = logging.getLogger("RakshaVisionTelegram")

class TelegramService:
    """
    Asynchronous Telegram Bot Notification Service for RakshaVision AI backend.
    Interacts directly with the Telegram Bot API using httpx without blocking the event loop.
    """

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        timeout: float = 10.0
    ):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        """Checks whether Telegram Bot Token and Chat ID are both available."""
        return bool(self.bot_token and self.chat_id)

    @property
    def api_base_url(self) -> str:
        """Constructs Telegram Bot API base URL."""
        return f"https://api.telegram.org/bot{self.bot_token}"

    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Sends a high-priority text message to the configured Telegram chat.
        Returns True if successful, False otherwise.
        """
        if not self.is_configured:
            logger.warning("Telegram Bot Token or Chat ID not configured. Skipping message dispatch.")
            return False

        url = f"{self.api_base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    logger.info(f"Telegram alert message successfully delivered to chat {self.chat_id}.")
                    return True
                else:
                    logger.error(f"Failed to send Telegram message. HTTP {response.status_code}: {response.text}")
                    return False
        except httpx.HTTPError as err:
            logger.error(f"HTTP error occurred while sending Telegram message: {err}")
            return False
        except Exception as exc:
            logger.error(f"Unexpected error while sending Telegram message: {exc}")
            return False

    async def send_photo(
        self,
        photo_path: str,
        caption: Optional[str] = None,
        parse_mode: str = "HTML"
    ) -> bool:
        """
        Sends an image snapshot alert to Telegram.
        """
        if not self.is_configured:
            logger.warning("Telegram Bot Token or Chat ID not configured. Skipping photo dispatch.")
            return False

        if not os.path.exists(photo_path):
            logger.error(f"Photo file not found: {photo_path}")
            return False

        url = f"{self.api_base_url}/sendPhoto"
        data = {"chat_id": self.chat_id, "parse_mode": parse_mode}
        if caption:
            data["caption"] = caption

        try:
            filename = os.path.basename(photo_path)
            with open(photo_path, "rb") as photo_file:
                files = {"photo": (filename, photo_file, "image/jpeg")}
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, data=data, files=files)
                    if response.status_code == 200:
                        logger.info(f"Telegram photo alert successfully delivered to chat {self.chat_id}.")
                        return True
                    else:
                        logger.error(f"Failed to send Telegram photo. HTTP {response.status_code}: {response.text}")
                        return False
        except httpx.HTTPError as err:
            logger.error(f"HTTP error occurred while sending Telegram photo: {err}")
            return False
        except Exception as exc:
            logger.error(f"Unexpected error while sending Telegram photo: {exc}")
            return False

    async def send_video(
        self,
        video_path: str,
        caption: Optional[str] = None,
        parse_mode: str = "HTML"
    ) -> bool:
        """
        Sends an MP4 video clip alert to Telegram using sendVideo API endpoint.
        """
        if not self.is_configured:
            logger.warning("Telegram Bot Token or Chat ID not configured. Skipping video clip dispatch.")
            return False

        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return False

        url = f"{self.api_base_url}/sendVideo"
        data = {"chat_id": self.chat_id, "parse_mode": parse_mode}
        if caption:
            data["caption"] = caption

        try:
            filename = os.path.basename(video_path)
            with open(video_path, "rb") as video_file:
                files = {"video": (filename, video_file, "video/mp4")}
                async with httpx.AsyncClient(timeout=self.timeout * 2) as client:
                    response = await client.post(url, data=data, files=files)
                    if response.status_code == 200:
                        logger.info(f"Telegram video clip alert successfully delivered to chat {self.chat_id}.")
                        return True
                    else:
                        logger.error(f"Failed to send Telegram video. HTTP {response.status_code}: {response.text}")
                        return False
        except httpx.HTTPError as err:
            logger.error(f"HTTP error occurred while sending Telegram video: {err}")
            return False
        except Exception as exc:
            logger.error(f"Unexpected error while sending Telegram video: {exc}")
            return False

    async def send_breach_alert(
        self,
        camera_id: int,
        object_type: str,
        confidence: float,
        timestamp: str,
        camera_name: Optional[str] = None,
        zone_name: Optional[str] = None,
        video_path: Optional[str] = None,
        photo_path: Optional[str] = None
    ) -> bool:
        """
        Sends a formatted high-priority perimeter breach alert to Telegram.
        Tries sending MP4 video clip first. If video sending fails or video_path is None,
        falls back to snapshot photo or text message.
        """
        cam_info = f"#{camera_id}"
        if camera_name:
            cam_info += f" ({camera_name})"

        caption = (
            "🚨 <b>PERIMETER BREACH ALERT</b> 🚨\n\n"
            f"<b>Camera:</b> {cam_info}\n"
            f"<b>Zone:</b> {zone_name or 'Restricted Sector'}\n"
            f"<b>Threat Detected:</b> {object_type.upper()}\n"
            f"<b>Confidence:</b> {confidence * 100:.1f}%\n"
            f"<b>Timestamp:</b> {timestamp}\n\n"
            "⚠️ <i>Immediate security team action required.</i>"
        )

        if video_path and os.path.exists(video_path):
            success = await self.send_video(video_path=video_path, caption=caption)
            if success:
                return True
            logger.warning("Sending video failed, falling back to snapshot photo...")

        if photo_path and os.path.exists(photo_path):
            success = await self.send_photo(photo_path=photo_path, caption=caption)
            if success:
                return True
            logger.warning("Sending photo failed, falling back to text message...")

        return await self.send_message(text=caption)


# Global default instance
_telegram_service_instance: Optional[TelegramService] = None

def get_telegram_service() -> TelegramService:
    """Returns singleton instance of TelegramService."""
    global _telegram_service_instance
    if _telegram_service_instance is None:
        _telegram_service_instance = TelegramService()
    return _telegram_service_instance
