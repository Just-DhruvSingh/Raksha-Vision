import os
import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.database import engine, get_db, Base, SessionLocal
from app import models, schemas
from app.api import camera_routes, zone_routes, incident_routes, alert_routes, analytics_routes, extra_routes
from app.vision.engine import VisionEngine, SNAPSHOTS_DIR, DATA_DIR

logger = logging.getLogger("RakshaVisionMain")
logging.basicConfig(level=logging.INFO)

# Initialize Database tables
Base.metadata.create_all(bind=engine)

# Setup Media directories
INCIDENT_MEDIA_DIR = os.path.join(DATA_DIR, "incident_media")
SAMPLE_VIDEOS_DIR = os.path.join(DATA_DIR, "sample_videos")

os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
os.makedirs(INCIDENT_MEDIA_DIR, exist_ok=True)
os.makedirs(SAMPLE_VIDEOS_DIR, exist_ok=True)

# ------------------------------------------------------------------------------
# Offline Seed Data Function (Runs if DB is empty)
# ------------------------------------------------------------------------------
def seed_demo_database():
    db = SessionLocal()
    try:
        if db.query(models.Camera).count() == 0:
            logger.info("Database is empty. Seeding offline demo cameras, zones, and incidents for evaluation...")
            
            # 1. Demo Cameras (matching frontend UI)
            cameras = [
                models.Camera(
                    id=1,
                    name="Main Gate Camera",
                    rtsp_url="sample_videos/gate_optical.mp4",
                    location="Main Entry Gate",
                    camera_type="PTZ Camera",
                    status="Online",
                    detections_count=42,
                    is_active=True
                ),
                models.Camera(
                    id=2,
                    name="Perimeter Zone B",
                    rtsp_url="sample_videos/perimeter_zone_b.mp4",
                    location="Border Perimeter",
                    camera_type="Fixed Camera",
                    status="Online",
                    detections_count=68,
                    is_active=True
                ),
                models.Camera(
                    id=4,
                    name="Watch Tower 02",
                    rtsp_url="sample_videos/watch_tower.mp4",
                    location="Watch Tower",
                    camera_type="PTZ Camera",
                    status="Online",
                    detections_count=31,
                    is_active=True
                ),
                models.Camera(
                    id=7,
                    name="Border Gate Alpha",
                    rtsp_url="sample_videos/gate_alpha.mp4",
                    location="Checkpoint Alpha",
                    camera_type="ANPR Camera",
                    status="Online",
                    detections_count=52,
                    is_active=True
                ),
                models.Camera(
                    id=11,
                    name="Checkpoint North",
                    rtsp_url="sample_videos/checkpoint_north.mp4",
                    location="North Checkpoint",
                    camera_type="Face Recognition",
                    status="Offline",
                    detections_count=34,
                    is_active=False
                ),
                models.Camera(
                    id=14,
                    name="Perimeter Zone C",
                    rtsp_url="sample_videos/perimeter_zone_c.mp4",
                    location="Border Perimeter",
                    camera_type="Fixed Camera",
                    status="Online",
                    detections_count=27,
                    is_active=True
                ),
            ]
            db.add_all(cameras)
            db.commit()

            # 2. Demo Restricted Polygon Zones
            zones = [
                models.Zone(
                    id=1,
                    camera_id=2,
                    name="Perimeter Buffer Zone B",
                    polygon_coords=[[100, 100], [500, 100], [520, 350], [80, 350]],
                    alert_type="intrusion",
                    is_active=True
                ),
                models.Zone(
                    id=2,
                    camera_id=7,
                    name="Restricted Entry Sector Alpha",
                    polygon_coords=[[150, 80], [450, 80], [480, 280], [120, 280]],
                    alert_type="intrusion",
                    is_active=True
                ),
                models.Zone(
                    id=3,
                    camera_id=1,
                    name="Virtual Perimeter Tripwire",
                    polygon_coords=[[50, 200], [600, 200], [600, 220], [50, 220]],
                    alert_type="tripwire",
                    is_active=True
                ),
            ]
            db.add_all(zones)
            db.commit()

            # 3. Demo Recent Incidents (matching frontend Incidents.jsx & Alerts.jsx)
            now = datetime.utcnow()
            incidents = [
                models.Incident(
                    id=1,
                    camera_id=2,
                    zone_id=1,
                    title="Perimeter Intrusion",
                    object_type="person",
                    confidence=0.94,
                    severity="CRITICAL",
                    description="Unauthorized movement detected near restricted border perimeter.",
                    bbox=[120.0, 140.0, 220.0, 320.0],
                    snapshot_path="snapshots/sample_breach_1.jpg",
                    status="investigating",
                    timestamp=now - timedelta(minutes=2)
                ),
                models.Incident(
                    id=2,
                    camera_id=7,
                    zone_id=2,
                    title="Unknown Vehicle Detected",
                    object_type="car",
                    confidence=0.91,
                    severity="HIGH",
                    description="Vehicle with an unrecognized number plate detected at checkpoint.",
                    bbox=[200.0, 160.0, 380.0, 290.0],
                    snapshot_path="snapshots/sample_breach_2.jpg",
                    status="under-review",
                    timestamp=now - timedelta(minutes=14)
                ),
                models.Incident(
                    id=3,
                    camera_id=11,
                    zone_id=None,
                    title="Watchlist Face Match",
                    object_type="person",
                    confidence=0.88,
                    severity="HIGH",
                    description="Facial recognition system generated a watchlist match.",
                    bbox=[150.0, 90.0, 260.0, 240.0],
                    snapshot_path="snapshots/sample_breach_3.jpg",
                    status="investigating",
                    timestamp=now - timedelta(minutes=32)
                ),
                models.Incident(
                    id=4,
                    camera_id=4,
                    zone_id=None,
                    title="Suspicious Object",
                    object_type="car",
                    confidence=0.85,
                    severity="MEDIUM",
                    description="AI object detection identified an unattended object.",
                    bbox=[280.0, 210.0, 360.0, 270.0],
                    snapshot_path="snapshots/sample_breach_4.jpg",
                    status="resolved",
                    timestamp=now - timedelta(hours=1)
                ),
            ]
            db.add_all(incidents)
            db.commit()
            logger.info("Demo database seeded successfully with 6 cameras, 3 zones, and 4 incidents.")
    except Exception as e:
        logger.error(f"Database seed error: {e}")
    finally:
        db.close()

seed_demo_database()

# ------------------------------------------------------------------------------
# FastAPI App Initialization
# ------------------------------------------------------------------------------
app = FastAPI(
    title="RakshaVision AI Backend",
    description="Edge-Native Perimeter Defense & Intrusion Detection System API (SIH26187)",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Media Endpoints
app.mount("/media", StaticFiles(directory=INCIDENT_MEDIA_DIR), name="media")
app.mount("/snapshots", StaticFiles(directory=SNAPSHOTS_DIR), name="snapshots")
app.mount("/incident_media", StaticFiles(directory=INCIDENT_MEDIA_DIR), name="incident_media")
app.mount("/sample_videos", StaticFiles(directory=SAMPLE_VIDEOS_DIR), name="sample_videos")

# Include Routers for /api and /api/v1 prefixes
app.include_router(camera_routes.router)
app.include_router(camera_routes.router, prefix="/api/v1")

app.include_router(zone_routes.router)
app.include_router(zone_routes.router, prefix="/api/v1")

app.include_router(incident_routes.router)
app.include_router(incident_routes.router, prefix="/api/v1")

app.include_router(alert_routes.router)
app.include_router(alert_routes.router, prefix="/api/v1")

app.include_router(analytics_routes.router)
app.include_router(analytics_routes.router, prefix="/api/v1")

app.include_router(extra_routes.router)

# ------------------------------------------------------------------------------
# WebSocket Real-Time Connection Manager
# ------------------------------------------------------------------------------
class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Active: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for ws in self.active_connections:
            try:
                await ws.send_json(message)
            except Exception:
                pass

ws_manager = WebSocketManager()

# Global Vision Engine instance
_vision_engine_instance: Optional[VisionEngine] = None

def get_vision_engine() -> VisionEngine:
    global _vision_engine_instance
    if _vision_engine_instance is None:
        _vision_engine_instance = VisionEngine(model_path="yolov8n.pt")
    return _vision_engine_instance

# ------------------------------------------------------------------------------
# Root & Health Check Endpoints
# ------------------------------------------------------------------------------
@app.get("/", tags=["Root"])
def root():
    return {
        "system": "RakshaVision AI Perimeter Defense System API",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
@app.get("/api/v1/health", tags=["Health"])
def health():
    return {
        "status": "online",
        "system": "RakshaVision AI Edge Backend",
        "database": "SQLite (WAL Mode)",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

# ------------------------------------------------------------------------------
# WebSocket Real-Time Telemetry & Alert Stream
# ------------------------------------------------------------------------------
@app.websocket("/ws/live")
@app.websocket("/ws/alerts")
@app.websocket("/api/v1/ws")
@app.websocket("/ws")
async def websocket_telemetry_stream(websocket: WebSocket):
    """
    Real-time WebSocket endpoint streaming detection telemetry, threat status, and alert broadcasts.
    """
    await ws_manager.connect(websocket)
    try:
        # Send initial connection handshake
        await websocket.send_json({
            "type": "handshake",
            "status": "connected",
            "system": "RakshaVision AI Telemetry Stream",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        while True:
            # Await client ping or message
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)
