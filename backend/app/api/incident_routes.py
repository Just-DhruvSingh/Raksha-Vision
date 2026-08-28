from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])

@router.get("", response_model=List[schemas.IncidentResponse])
def list_incidents(
    camera_id: Optional[int] = Query(None, description="Filter by camera ID"),
    zone_id: Optional[int] = Query(None, description="Filter by zone ID"),
    status: Optional[str] = Query(None, description="Filter by status ('investigating', 'under-review', 'resolved', 'unacknowledged', 'acknowledged', 'dismissed')"),
    severity: Optional[str] = Query(None, description="Filter by severity ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')"),
    object_type: Optional[str] = Query(None, description="Filter by object type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Retrieve security breach incidents with optional filtering."""
    query = db.query(models.Incident)

    if camera_id is not None:
        query = query.filter(models.Incident.camera_id == camera_id)
    if zone_id is not None:
        query = query.filter(models.Incident.zone_id == zone_id)
    if status is not None:
        query = query.filter(models.Incident.status == status)
    if severity is not None:
        query = query.filter(models.Incident.severity == severity.upper())
    if object_type is not None:
        query = query.filter(models.Incident.object_type == object_type)

    return query.order_by(desc(models.Incident.timestamp)).offset(skip).limit(limit).all()

@router.get("/{incident_id}", response_model=schemas.IncidentResponse)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    """Retrieve details for a specific incident."""
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident with ID {incident_id} not found.")
    return incident

@router.post("", response_model=schemas.IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(incident_in: schemas.IncidentCreate, db: Session = Depends(get_db)):
    """Manually record a new security incident."""
    camera = db.query(models.Camera).filter(models.Camera.id == incident_in.camera_id).first()
    if not camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Camera with ID {incident_in.camera_id} does not exist.")

    incident = models.Incident(
        camera_id=incident_in.camera_id,
        zone_id=incident_in.zone_id,
        title=incident_in.title or "Perimeter Intrusion",
        object_type=incident_in.object_type,
        confidence=incident_in.confidence,
        severity=incident_in.severity or "CRITICAL",
        description=incident_in.description,
        bbox=incident_in.bbox,
        snapshot_path=incident_in.snapshot_path,
        video_clip_path=incident_in.video_clip_path,
        status=incident_in.status,
        timestamp=datetime.utcnow()
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident

@router.put("/{incident_id}", response_model=schemas.IncidentResponse)
def update_incident(incident_id: int, incident_in: schemas.IncidentUpdate, db: Session = Depends(get_db)):
    """Update incident status or severity."""
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident with ID {incident_id} not found.")

    if incident_in.status is not None:
        incident.status = incident_in.status
    if incident_in.severity is not None:
        incident.severity = incident_in.severity
    if incident_in.title is not None:
        incident.title = incident_in.title

    db.commit()
    db.refresh(incident)
    return incident

@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_incident(incident_id: int, db: Session = Depends(get_db)):
    """Delete an incident record."""
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident with ID {incident_id} not found.")

    db.delete(incident)
    db.commit()
    return None
