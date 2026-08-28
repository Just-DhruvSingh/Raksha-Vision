from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])

@router.get("", response_model=List[schemas.AlertItemResponse])
def list_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')"),
    status: Optional[str] = Query(None, description="Filter by status ('ACTIVE', 'ACKNOWLEDGED')"),
    search: Optional[str] = Query(None, description="Search query across alert fields"),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Retrieve formatted real-time security alerts matching frontend Alerts.jsx structure.
    """
    query = db.query(models.Incident).join(models.Camera, models.Incident.camera_id == models.Camera.id)

    if severity and severity.upper() != "ALL":
        query = query.filter(models.Incident.severity == severity.upper())

    if status:
        if status.upper() == "ACTIVE":
            query = query.filter(models.Incident.status.in_(["unacknowledged", "ACTIVE", "investigating", "under-review"]))
        elif status.upper() == "ACKNOWLEDGED":
            query = query.filter(models.Incident.status.in_(["acknowledged", "ACKNOWLEDGED", "resolved", "dismissed"]))

    incidents = query.order_by(desc(models.Incident.timestamp)).offset(skip).limit(limit).all()

    alert_list = []
    for inc in incidents:
        cam_name = inc.camera.name if inc.camera else f"CAM-{inc.camera_id}"
        cam_loc = inc.camera.location if inc.camera and inc.camera.location else "Perimeter Sector"
        
        is_ack = inc.status in ["acknowledged", "ACKNOWLEDGED", "resolved", "dismissed"]
        
        item = schemas.AlertItemResponse(
            id=f"ALT-{inc.id:03d}",
            type=inc.title or f"{inc.object_type.capitalize()} Detected",
            camera=f"CAM-{inc.camera_id:02d}",
            camera_id=inc.camera_id,
            location=cam_loc,
            time=inc.timestamp.strftime("%H:%M:%S UTC"),
            severity=inc.severity or "CRITICAL",
            description=inc.description or f"Unauthorized {inc.object_type} movement detected with {inc.confidence*100:.1f}% confidence.",
            status="ACKNOWLEDGED" if is_ack else "ACTIVE",
            snapshot_path=inc.snapshot_path
        )
        
        if search:
            s = search.lower()
            if not (s in item.type.lower() or s in item.location.lower() or s in item.camera.lower() or s in item.id.lower()):
                continue
                
        alert_list.append(item)

    return alert_list

@router.put("/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str, db: Session = Depends(get_db)):
    """Acknowledge an active alert."""
    try:
        inc_id = int(alert_id.replace("ALT-", "").replace("#", ""))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid alert ID format. Expected 'ALT-001' or integer.")

    incident = db.query(models.Incident).filter(models.Incident.id == inc_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Alert with ID {alert_id} not found.")

    incident.status = "ACKNOWLEDGED"
    db.commit()
    return {"status": "success", "alert_id": alert_id, "state": "ACKNOWLEDGED"}
