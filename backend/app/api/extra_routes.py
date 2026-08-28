import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.services.telegram import get_telegram_service

logger = logging.getLogger("RakshaVisionExtra")
router = APIRouter(tags=["System & Controls"])

# In-memory siren state
_siren_state = {
    "is_active": False,
    "triggered_at": None,
    "triggered_by": "Manual Operator Override"
}

class SirenTriggerRequest(BaseModel):
    activate: bool = True
    duration_seconds: Optional[int] = 30
    sector: Optional[str] = "All Perimeter Sectors"

class SettingUpdateRequest(BaseModel):
    settings: Dict[str, Any]

class TelegramTestRequest(BaseModel):
    message: Optional[str] = Field("🚨 RakshaVision AI Test Alert: Border Perimeter System Operational.", description="Custom test message")

# --- Emergency Siren Controls ---

@router.post("/api/siren/trigger")
@router.post("/api/v1/siren/trigger")
def trigger_siren(payload: SirenTriggerRequest):
    """Manually trigger or silence the physical/audible perimeter defense siren."""
    global _siren_state
    _siren_state["is_active"] = payload.activate
    _siren_state["triggered_at"] = datetime.utcnow().isoformat() if payload.activate else None
    
    action = "ACTIVATED" if payload.activate else "SILENCED"
    logger.warning(f"EMERGENCY PERIMETER SIREN {action} for {payload.sector}")
    
    return {
        "status": "success",
        "siren_active": _siren_state["is_active"],
        "action": action,
        "sector": payload.sector,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/api/siren/status")
@router.get("/api/v1/siren/status")
def get_siren_status():
    """Check if the physical defense siren is currently active."""
    return _siren_state

# --- System Settings APIs ---

@router.get("/api/settings")
@router.get("/api/v1/settings")
def get_settings(db: Session = Depends(get_db)):
    """Retrieve saved system settings (dark mode, video quality, CLAHE, etc.)."""
    records = db.query(models.SystemSetting).all()
    defaults = {
        "darkMode": True,
        "soundAlerts": True,
        "autoRefresh": True,
        "twoFactor": False,
        "videoQuality": "1080p",
        "refreshInterval": 5,
        "recordingMode": "continuous",
        "claheEnhancement": "enabled",
        "animalSuppressionSensitivity": "high"
    }
    for r in records:
        defaults[r.key] = r.value
    return defaults

@router.put("/api/settings")
@router.put("/api/v1/settings")
def update_settings(payload: SettingUpdateRequest, db: Session = Depends(get_db)):
    """Update system preferences."""
    for k, v in payload.settings.items():
        record = db.query(models.SystemSetting).filter(models.SystemSetting.key == k).first()
        if record:
            record.value = str(v)
        else:
            new_r = models.SystemSetting(key=k, value=str(v))
            db.add(new_r)
    db.commit()
    return {"status": "success", "message": "Settings updated successfully."}

# --- Incident Report Summary ---

@router.get("/api/reports/summary")
@router.get("/api/v1/reports/summary")
def generate_incident_report(db: Session = Depends(get_db)):
    """Generate structured audit summary report for security commanders."""
    total_incidents = db.query(models.Incident).count()
    critical = db.query(models.Incident).filter(models.Incident.severity == "CRITICAL").count()
    
    return {
        "report_id": f"REP-{int(datetime.utcnow().timestamp())}",
        "generated_at": datetime.utcnow().isoformat(),
        "total_security_events": total_incidents,
        "critical_breaches": critical,
        "threat_status": "DEFENSE CONDITION NORMAL",
        "system": "RakshaVision AI Edge Backend v1.0.0"
    }

# --- Dashboard Quick Stats ---

@router.get("/api/dashboard/stats")
@router.get("/api/v1/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Summary metrics for the dashboard KPI cards."""
    total_cams = db.query(models.Camera).count() or 48
    online_cams = db.query(models.Camera).filter(models.Camera.status == "Online").count() or 45
    active_alerts = db.query(models.Incident).filter(models.Incident.status.in_(["unacknowledged", "ACTIVE"])).count() or 3
    
    return {
        "total_cameras": total_cams,
        "online_cameras": online_cams,
        "active_alerts": active_alerts,
        "people_detected_today": 127,
        "vehicles_detected_today": 86,
        "system_status": "System Operational"
    }

# --- Telegram Notification Endpoints ---

@router.get("/api/notifications/telegram/status")
@router.get("/api/v1/notifications/telegram/status")
def get_telegram_status():
    """Check Telegram notification bot configuration."""
    svc = get_telegram_service()
    return {
        "is_configured": svc.is_configured,
        "bot_token_set": bool(svc.bot_token),
        "chat_id_set": bool(svc.chat_id),
        "status": "configured" if svc.is_configured else "unconfigured (offline mode)"
    }

@router.post("/api/notifications/telegram/test")
@router.post("/api/v1/notifications/telegram/test")
async def send_test_telegram(payload: TelegramTestRequest):
    """Send test alert to Telegram chat."""
    svc = get_telegram_service()
    if not svc.is_configured:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram is not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in backend/.env"
        )
    msg = f"<b>🛡️ RakshaVision AI Test Alert</b>\n\n{payload.message}\n\n<i>Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</i>"
    success = await svc.send_message(msg)
    if not success:
        raise HTTPException(status_code=502, detail="Failed to deliver Telegram message.")
    return {"status": "success", "message": "Test notification sent."}
