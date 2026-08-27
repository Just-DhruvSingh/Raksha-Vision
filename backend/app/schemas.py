from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

# --- Camera Schemas ---

class CameraBase(BaseModel):
    name: str = Field(..., max_length=100, json_schema_extra={"example": "North Gate Optical"})
    rtsp_url: str = Field(..., json_schema_extra={"example": "rtsp://192.168.1.100:554/stream1"})
    location: Optional[str] = Field(None, json_schema_extra={"example": "Sector 4 - Perimeter Wall"})
    is_active: bool = True

class CameraCreate(CameraBase):
    pass

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    rtsp_url: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None

class CameraResponse(CameraBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Zone Schemas ---

class ZoneBase(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "High Security Buffer Zone A"})
    polygon_coords: List[List[float]] = Field(
        ...,
        json_schema_extra={"example": [[100.0, 100.0], [400.0, 100.0], [400.0, 400.0], [100.0, 400.0]]},
        description="List of 2D points [x, y] defining polygon vertices."
    )
    alert_type: str = Field("intrusion", json_schema_extra={"example": "intrusion"})
    is_active: bool = True

    @field_validator("polygon_coords")
    @classmethod
    def validate_polygon(cls, v: List[List[float]]) -> List[List[float]]:
        if len(v) < 3:
            raise ValueError("Polygon must contain at least 3 vertices.")
        for pt in v:
            if len(pt) != 2:
                raise ValueError("Each polygon coordinate point must be a 2D [x, y] pair.")
        return v

class ZoneCreate(ZoneBase):
    camera_id: int

class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    polygon_coords: Optional[List[List[float]]] = None
    alert_type: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("polygon_coords")
    @classmethod
    def validate_polygon(cls, v: Optional[List[List[float]]]) -> Optional[List[List[float]]]:
        if v is not None:
            if len(v) < 3:
                raise ValueError("Polygon must contain at least 3 vertices.")
            for pt in v:
                if len(pt) != 2:
                    raise ValueError("Each polygon coordinate point must be a 2D [x, y] pair.")
        return v

class ZoneResponse(ZoneBase):
    id: int
    camera_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Incident Schemas ---

class IncidentBase(BaseModel):
    camera_id: int
    zone_id: Optional[int] = None
    object_type: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]
    snapshot_path: Optional[str] = None
    video_clip_path: Optional[str] = None
    status: str = "unacknowledged"

class IncidentCreate(IncidentBase):
    pass

class IncidentUpdate(BaseModel):
    status: str

class IncidentResponse(IncidentBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Real-time WebSocket Payload Schemas ---

class AlertPayload(BaseModel):
    incident_id: int
    camera_id: int
    camera_name: str
    zone_id: Optional[int]
    zone_name: Optional[str]
    object_type: str
    confidence: float
    bbox: List[float]
    snapshot_url: Optional[str]
    timestamp: str
