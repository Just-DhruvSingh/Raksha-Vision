"""
Services package for RakshaVision AI backend.
"""
from app.services.telegram import TelegramService, get_telegram_service

__all__ = ["TelegramService", "get_telegram_service"]
