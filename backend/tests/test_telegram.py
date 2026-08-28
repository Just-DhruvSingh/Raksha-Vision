import os
import sys
import tempfile
import pytest
import numpy as np
from unittest.mock import patch, AsyncMock, MagicMock

# Ensure app package is on python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.telegram import TelegramService, get_telegram_service
from app.vision.engine import generate_video_clip, dispatch_telegram_alert_async


@pytest.mark.asyncio
async def test_telegram_service_unconfigured(monkeypatch):
    """Test that TelegramService handles missing environment variables gracefully."""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    service = TelegramService()
    assert service.is_configured is False

    # Dispatching operations should return False without raising exceptions
    msg_res = await service.send_message("Test breach message")
    assert msg_res is False

    photo_res = await service.send_photo("/nonexistent/photo.jpg")
    assert photo_res is False

    video_res = await service.send_video("/nonexistent/video.mp4")
    assert video_res is False

    breach_res = await service.send_breach_alert(
        camera_id=1,
        object_type="person",
        confidence=0.95,
        timestamp="2026-08-28T20:00:00Z"
    )
    assert breach_res is False


@pytest.mark.asyncio
async def test_telegram_service_send_message_success(monkeypatch):
    """Test successful text message dispatch via httpx mock."""
    service = TelegramService(bot_token="test_token_123", chat_id="123456789")
    assert service.is_configured is True

    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        res = await service.send_message("🚨 Test Breach Detected!")
        assert res is True
        mock_post.assert_called_once()
        call_url = mock_post.call_args[0][0]
        assert call_url == "https://api.telegram.org/bottest_token_123/sendMessage"


@pytest.mark.asyncio
async def test_telegram_service_send_media_success(monkeypatch):
    """Test sending snapshot photo and 5-second MP4 video clip alerts via httpx mock."""
    service = TelegramService(bot_token="test_token_123", chat_id="123456789")

    mock_response = MagicMock()
    mock_response.status_code = 200

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_photo, \
         tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_video:
        
        tmp_photo.write(b"fake_jpeg_bytes")
        tmp_photo.flush()
        tmp_video.write(b"fake_mp4_bytes")
        tmp_video.flush()

        try:
            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_response

                # Test photo send
                photo_res = await service.send_photo(tmp_photo.name, caption="Test Photo Alert")
                assert photo_res is True

                # Test video send
                video_res = await service.send_video(tmp_video.name, caption="Test Video Alert")
                assert video_res is True

                # Test high-level breach alert dispatch (video priority)
                breach_res = await service.send_breach_alert(
                    camera_id=2,
                    object_type="person",
                    confidence=0.91,
                    timestamp="2026-08-28T20:10:00Z",
                    camera_name="East Gate",
                    zone_name="Perimeter Fence A",
                    video_path=tmp_video.name,
                    photo_path=tmp_photo.name
                )
                assert breach_res is True
        finally:
            if os.path.exists(tmp_photo.name):
                os.remove(tmp_photo.name)
            if os.path.exists(tmp_video.name):
                os.remove(tmp_video.name)


@pytest.mark.asyncio
async def test_telegram_service_api_error_resilience():
    """Test resilience against Telegram API errors or timeouts."""
    service = TelegramService(bot_token="test_token_123", chat_id="123456789")

    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = '{"ok": false, "error_code": 401, "description": "Unauthorized"}'

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        res = await service.send_message("Test message")
        assert res is False


def test_generate_video_clip():
    """Test video clip generation from synthetic BGR frames."""
    frames = [np.zeros((240, 320, 3), dtype=np.uint8) for _ in range(15)]
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        output_path = tmp.name

    try:
        res_path = generate_video_clip(frames, output_path, fps=15.0)
        assert res_path is not None
        assert os.path.exists(res_path)
        assert os.path.getsize(res_path) > 0
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


def test_dispatch_telegram_alert_async(monkeypatch):
    """Test non-blocking async dispatch wrapper."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token_123")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456789")

    alert_data = {
        "camera_id": 1,
        "object_type": "person",
        "confidence": 0.88,
        "timestamp": "2026-08-28T20:20:00Z"
    }

    with patch.object(TelegramService, "send_breach_alert", new_callable=AsyncMock) as mock_breach:
        mock_breach.return_value = True
        dispatch_telegram_alert_async(alert_data)
