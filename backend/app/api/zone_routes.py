from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/zones", tags=["Perimeter Zones"])

@router.get("", response_model=List[schemas.ZoneResponse])
def list_zones(camera_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieve all defined perimeter tripwires/intrusion zones, optionally filtered by camera."""
    query = db.query(models.Zone)
    if camera_id is not None:
        query = query.filter(models.Zone.camera_id == camera_id)
    return query.offset(skip).limit(limit).all()

@router.post("", response_model=schemas.ZoneResponse, status_code=201)
def create_zone(zone_in: schemas.ZoneCreate, db: Session = Depends(get_db)):
    """Create a polygonal security zone for a camera stream."""
    camera = db.query(models.Camera).filter(models.Camera.id == zone_in.camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail=f"Camera with ID {zone_in.camera_id} does not exist.")

    zone = models.Zone(**zone_in.model_dump())
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone

@router.get("/{zone_id}", response_model=schemas.ZoneResponse)
def get_zone(zone_id: int, db: Session = Depends(get_db)):
    """Get details for a specific perimeter zone."""
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone with ID {zone_id} not found.")
    return zone

@router.put("/{zone_id}", response_model=schemas.ZoneResponse)
def update_zone(zone_id: int, zone_in: schemas.ZoneUpdate, db: Session = Depends(get_db)):
    """Update polygonal coordinates or attributes of a zone."""
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone with ID {zone_id} not found.")

    update_data = zone_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(zone, field, value)

    db.commit()
    db.refresh(zone)
    return zone

@router.delete("/{zone_id}", status_code=204)
def delete_zone(zone_id: int, db: Session = Depends(get_db)):
    """Delete a perimeter zone."""
    zone = db.query(models.Zone).filter(models.Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone with ID {zone_id} not found.")

    db.delete(zone)
    db.commit()
    return None
