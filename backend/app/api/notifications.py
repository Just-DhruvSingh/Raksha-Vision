import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("RakshaVisionNotifications")

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

# ------------------------------------------------------------------------------
# Async Telegram Notification Utilities (using httpx)
# ------------------------------------------------------------------------------

def _get_telegram_config():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    return bot_token, chat_id

async def send_telegram_alert(text: str, parse_mode: str = "HTML") -> bool:
    """
    Sends an async high-priority text message to the configured Telegram chat using httpx.
    """
    bot_token, chat_id = _get_telegram_config()
    if not bot_token or not chat_id or "dummy" in bot_token.lower():
        logger.info("Telegram Bot Token or Chat ID not configured. Skipping alert.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                logger.info("Telegram text alert delivered successfully.")
                return True
            else:
                logger.error(f"Telegram error {response.status_code}: {response.text}")
                return False
    except Exception as exc:
        logger.error(f"Telegram dispatch error: {exc}")
        return False

async def send_telegram_photo(photo_path: str, caption: Optional[str] = None, parse_mode: str = "HTML") -> bool:
    """
    Sends an image snapshot alert to Telegram using sendPhoto.
    """
    bot_token, chat_id = _get_telegram_config()
    if not bot_token or not chat_id or "dummy" in bot_token.lower():
        return False

    if not photo_path or not os.path.exists(photo_path):
        return await send_telegram_alert(caption or "🚨 RakshaVision AI Intrusion Alert")

    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    data = {"chat_id": chat_id, "parse_mode": parse_mode}
    if caption:
        data["caption"] = caption

    try:
        filename = os.path.basename(photo_path)
        with open(photo_path, "rb") as f:
            files = {"photo": (filename, f, "image/jpeg")}
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.post(url, data=data, files=files)
                return response.status_code == 200
    except Exception as exc:
        logger.error(f"Telegram photo dispatch error: {exc}")
        return await send_telegram_alert(caption or "🚨 RakshaVision AI Alert")

async def send_telegram_video(video_path: str, caption: Optional[str] = None, parse_mode: str = "HTML") -> bool:
    """
    Sends an MP4 video clip breach alert to Telegram using sendVideo.
    """
    bot_token, chat_id = _get_telegram_config()
    if not bot_token or not chat_id or "dummy" in bot_token.lower():
        return False

    if not video_path or not os.path.exists(video_path):
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    data = {"chat_id": chat_id, "parse_mode": parse_mode}
    if caption:
        data["caption"] = caption

    try:
        filename = os.path.basename(video_path)
        with open(video_path, "rb") as f:
            files = {"video": (filename, f, "video/mp4")}
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(url, data=data, files=files)
                if response.status_code == 200:
                    logger.info("Telegram video clip alert delivered successfully.")
                    return True
                else:
                    logger.warning(f"Telegram video upload failed: {response.text}")
                    return False
    except Exception as exc:
        logger.error(f"Telegram video dispatch error: {exc}")
        return False

# ------------------------------------------------------------------------------
# API Endpoints
# ------------------------------------------------------------------------------

class TelegramTestPayload(BaseModel):
    message: Optional[str] = Field("🚨 RakshaVision AI Test Alert: Border Defense System Operational.")

@router.get("/telegram/status")
def get_status():
    bot_token, chat_id = _get_telegram_config()
    is_conf = bool(bot_token and chat_id and "dummy" not in bot_token.lower())
    return {
        "is_configured": is_conf,
        "bot_token_set": bool(bot_token),
        "chat_id_set": bool(chat_id),
        "status": "ready" if is_conf else "offline/dummy_mode"
    }

@router.post("/telegram/test")
async def test_telegram(payload: TelegramTestPayload):
    text = (
        f"<b>🛡️ RakshaVision AI — System Test Alert</b>\n\n"
        f"{payload.message}\n\n"
        f"<i>Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</i>"
    )
    success = await send_telegram_alert(text)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram is not configured with a valid token/chat_id. Update backend/.env."
        )
    return {"status": "success", "message": "Test message sent to Telegram."}
