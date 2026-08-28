from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/api/cameras", tags=["Cameras"])

@router.get("", response_model=List[schemas.CameraResponse])
def list_cameras(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieve all configured surveillance cameras."""
    cameras = db.query(models.Camera).offset(skip).limit(limit).all()
    return cameras

@router.post("", response_model=schemas.CameraResponse, status_code=status.HTTP_201_CREATED)
def create_camera(camera_in: schemas.CameraCreate, db: Session = Depends(get_db)):
    """Register and deploy a new camera stream."""
    camera = models.Camera(**camera_in.model_dump())
    db.add(camera)
    db.commit()
    db.refresh(camera)
    return camera

@router.get("/{camera_id}", response_model=schemas.CameraResponse)
def get_camera(camera_id: int, db: Session = Depends(get_db)):
    """Get details for a specific camera."""
    camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Camera with ID {camera_id} not found.")
    return camera

@router.put("/{camera_id}", response_model=schemas.CameraResponse)
def update_camera(camera_id: int, camera_in: schemas.CameraUpdate, db: Session = Depends(get_db)):
    """Update configuration for an existing camera."""
    camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Camera with ID {camera_id} not found.")

    update_data = camera_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(camera, field, value)

    db.commit()
    db.refresh(camera)
    return camera

@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_camera(camera_id: int, db: Session = Depends(get_db)):
    """Delete a camera configuration."""
    camera = db.query(models.Camera).filter(models.Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Camera with ID {camera_id} not found.")

    db.delete(camera)
    db.commit()
    return None
