from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    rtsp_url = Column(String(500), nullable=False)
    location = Column(String(200), nullable=True)
    camera_type = Column(String(50), default="Fixed Camera")  # 'PTZ Camera', 'Fixed Camera', 'ANPR Camera', 'Face Recognition'
    status = Column(String(50), default="Online")  # 'Online', 'Offline', 'Warning'
    detections_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    zones = relationship("Zone", back_populates="camera", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="camera", cascade="all, delete-orphan")

class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    polygon_coords = Column(JSON, nullable=False)  # [[x,y], ...]
    alert_type = Column(String(50), default="intrusion")  # 'intrusion', 'tripwire'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    camera = relationship("Camera", back_populates="zones")
    incidents = relationship("Incident", back_populates="zone")

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(200), default="Perimeter Intrusion")
    object_type = Column(String(50), nullable=False)  # 'person', 'car', etc.
    confidence = Column(Float, nullable=False)
    severity = Column(String(50), default="CRITICAL")  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    description = Column(Text, nullable=True)
    bbox = Column(JSON, nullable=False)  # [x1, y1, x2, y2]
    snapshot_path = Column(String(500), nullable=True)
    video_clip_path = Column(String(500), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(String(50), default="unacknowledged")  # 'unacknowledged', 'acknowledged', 'investigating', 'under-review', 'resolved', 'dismissed'

    # Relationships
    camera = relationship("Camera", back_populates="incidents")
    zone = relationship("Zone", back_populates="incidents")

class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(String(500), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
