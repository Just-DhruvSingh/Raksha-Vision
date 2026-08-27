import os
import logging
from typing import List, Optional
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.database import engine, get_db, Base
from app import models, schemas
from app.api import camera_routes, zone_routes
from app.vision.engine import VisionEngine, SNAPSHOTS_DIR

logger = logging.getLogger("RakshaVisionMain")
logging.basicConfig(level=logging.INFO)

# Initialize Database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RakshaVision AI Backend",
    description="Edge-Native Perimeter Defense & Intrusion Detection System API (SIH26187)",
    version="1.0.0"
)

# CORS Configuration for local edge dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static file directory for incident snapshot retrieval
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
app.mount("/snapshots", StaticFiles(directory=SNAPSHOTS_DIR), name="snapshots")

# Include Routers
app.include_router(camera_routes.router)
app.include_router(zone_routes.router)

# WebSocket Connection Manager for Real-Time Alert Broadcasts
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Remaining active connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting WebSocket message: {e}")

ws_manager = ConnectionManager()

# Global lazy vision engine instance
_vision_engine_instance: Optional[VisionEngine] = None

def get_vision_engine() -> VisionEngine:
    global _vision_engine_instance
    if _vision_engine_instance is None:
        _vision_engine_instance = VisionEngine(model_path="yolov8n.pt")
    return _vision_engine_instance

# --- Health & Base Endpoints ---

@app.get("/", tags=["Root"])
def root_welcome():
    """Root endpoint providing system info and links to documentation."""
    return {
        "system": "RakshaVision AI Perimeter Defense System API",
        "status": "online",
        "documentation": "/docs",
        "health": "/health",
        "version": "1.0.0"
    }

@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check():
    """System health check endpoint."""
    return {
        "status": "online",
        "system": "RakshaVision AI Edge Backend",
        "database": "SQLite (WAL Mode)",
        "version": "1.0.0"
    }

# --- Incident Management Endpoints ---

@app.get("/api/incidents", response_model=List[schemas.IncidentResponse], tags=["Incidents"])
def list_incidents(
    camera_id: Optional[int] = Query(None, description="Filter incidents by Camera ID"),
    status: Optional[str] = Query(None, description="Filter incidents by status (unacknowledged/acknowledged/dismissed)"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Retrieve security breach incidents with optional camera or status filtering."""
    query = db.query(models.Incident)
    if camera_id is not None:
        query = query.filter(models.Incident.camera_id == camera_id)
    if status is not None:
        query = query.filter(models.Incident.status == status)

    return query.order_by(models.Incident.timestamp.desc()).offset(skip).limit(limit).all()

@app.put("/api/incidents/{incident_id}", response_model=schemas.IncidentResponse, tags=["Incidents"])
def update_incident_status(
    incident_id: int,
    incident_in: schemas.IncidentUpdate,
    db: Session = Depends(get_db)
):
    """Acknowledge or dismiss an incident alert."""
    incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident with ID {incident_id} not found.")

    incident.status = incident_in.status
    db.commit()
    db.refresh(incident)
    return incident

# --- Real-Time Alert WebSocket Endpoint ---

@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """Real-time WebSocket endpoint for receiving live perimeter breach notifications."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive & await client messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
