import os
import time
import base64
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, AsyncGenerator, Tuple
import cv2
import numpy as np
from ultralytics import YOLO

from app.vision.spatial import is_point_in_polygon, calculate_bottom_center

logger = logging.getLogger("RakshaVisionEngine")
logging.basicConfig(level=logging.INFO)

# Data & Snapshot Storage Setup
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
SNAPSHOTS_DIR = os.path.join(DATA_DIR, "snapshots")
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

# COCO Class Mappings & Threat Definitions
THREAT_CLASSES = {"person", "car", "motorcycle", "bus", "truck"}
BENIGN_ANIMALS = {"cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "bird"}

def apply_clahe_lowlight(frame: np.ndarray, clip_limit: float = 2.0, tile_grid_size: Tuple[int, int] = (8, 8)) -> np.ndarray:
    """
    Applies CLAHE (Contrast Limited Adaptive Histogram Equalization) on the L-channel 
    in LAB color space to enhance low-light/night-vision/thermal contrast without adding latency.
    """
    if frame is None or frame.size == 0:
        return frame
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    cl = clahe.apply(l_channel)
    limg = cv2.merge((cl, a_channel, b_channel))
    return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)


class VisionEngine:
    def __init__(self, model_path: str = "yolov8n.pt", confidence_threshold: float = 0.4):
        """Initializes OpenCV + YOLOv8 + ByteTrack object tracking engine."""
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        logger.info(f"Initializing VisionEngine with YOLO model: {model_path}")
        self.model = YOLO(model_path)
        self.active_alert_ids = set()

    def process_frame(
        self,
        frame: np.ndarray,
        zones: Optional[List[Dict[str, Any]]] = None,
        camera_id: int = 1,
        alert_callback: Optional[Any] = None,
        enable_clahe: bool = False
    ) -> Dict[str, Any]:
        """
        Processes a single BGR image frame, performs tracking, spatial polygon evaluation,
        draws annotations, and returns detection telemetry.
        """
        if frame is None or frame.size == 0:
            return {"detections": [], "alerts": [], "annotated_frame": frame, "breach_detected": False}

        if enable_clahe:
            frame = apply_clahe_lowlight(frame)

        if zones is None:
            zones = []

        # Perform YOLO tracking with ByteTrack
        results = self.model.track(
            source=frame,
            conf=self.confidence_threshold,
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False
        )

        detections = []
        alerts = []
        annotated_frame = frame.copy()
        breach_detected = False

        if not results or len(results) == 0:
            return {
                "detections": [],
                "alerts": [],
                "annotated_frame": annotated_frame,
                "breach_detected": False
            }

        res = results[0]
        boxes = res.boxes

        # Track breached zone IDs to highlight polygon overlays
        breached_zone_ids = set()

        if boxes is not None and len(boxes) > 0:
            for box in boxes:
                xyxy = box.xyxy[0].cpu().numpy().tolist()  # [x1, y1, x2, y2]
                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                class_name = self.model.names.get(cls_id, f"class_{cls_id}").lower()

                # False Alarm Suppression: Skip benign animals
                if class_name in BENIGN_ANIMALS:
                    continue

                track_id = int(box.id[0].cpu().numpy()) if box.id is not None else None

                # Compute bottom-center feet/contact point
                bottom_center = calculate_bottom_center(xyxy)

                # Spatial breach checking for threat classes
                is_breaching = False
                if class_name in THREAT_CLASSES:
                    for z in zones:
                        poly = z.get("polygon_coords") or z.get("polygon") or []
                        if len(poly) >= 3:
                            if is_point_in_polygon(bottom_center, poly):
                                is_breaching = True
                                breach_detected = True
                                if "id" in z:
                                    breached_zone_ids.add(z["id"])
                                break

                det = {
                    "track_id": track_id if track_id is not None else -1,
                    "class_label": class_name,
                    "confidence": round(conf, 3),
                    "bbox": [round(c, 1) for c in xyxy],
                    "is_breaching": is_breaching
                }
                detections.append(det)

                # Draw bounding box
                x1, y1, x2, y2 = [int(c) for c in xyxy]
                color = (0, 0, 255) if is_breaching else (0, 255, 0)  # Red if breaching, green otherwise

                label = f"{class_name}"
                if track_id is not None:
                    label += f" #{track_id}"
                label += f" {conf:.2f}"
                if is_breaching:
                    label += " [BREACH]"

                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(annotated_frame, label, (x1, max(y1 - 10, 15)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                # Handle snapshot alert creation
                if is_breaching:
                    alert_key = (track_id, camera_id) if track_id is not None else (time.time(), camera_id)
                    if alert_key not in self.active_alert_ids:
                        self.active_alert_ids.add(alert_key)
                        snapshot_filename = f"incident_cam{camera_id}_{int(time.time()*1000)}.jpg"
                        snapshot_path = os.path.join(SNAPSHOTS_DIR, snapshot_filename)
                        cv2.imwrite(snapshot_path, annotated_frame)

                        alert_data = {
                            "camera_id": camera_id,
                            "object_type": class_name,
                            "confidence": round(conf, 3),
                            "bbox": [round(c, 1) for c in xyxy],
                            "snapshot_path": snapshot_path,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        alerts.append(alert_data)
                        if alert_callback:
                            try:
                                alert_callback(alert_data)
                            except Exception as e:
                                logger.error(f"Alert callback error: {e}")

        # Draw semi-transparent polygon zones
        if zones:
            overlay = annotated_frame.copy()
            for z in zones:
                poly = z.get("polygon_coords") or z.get("polygon") or []
                if len(poly) >= 3:
                    pts = np.array(poly, np.int32).reshape((-1, 1, 2))
                    zone_id = z.get("id")
                    is_zone_breached = zone_id in breached_zone_ids if zone_id else breach_detected
                    
                    # Fill color: Red if breached, Yellow if idle
                    fill_color = (0, 0, 220) if is_zone_breached else (0, 220, 255)
                    line_color = (0, 0, 255) if is_zone_breached else (0, 255, 255)

                    cv2.fillPoly(overlay, [pts], fill_color)
                    cv2.polylines(annotated_frame, [pts], isClosed=True, color=line_color, thickness=2)

                    # Zone label
                    cx = int(np.mean([p[0] for p in poly]))
                    cy = int(np.mean([p[1] for p in poly]))
                    cv2.putText(annotated_frame, z.get("name", "RESTRICTED ZONE"), (cx - 40, cy),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

            # Blend semi-transparent overlay (25% opacity)
            cv2.addWeighted(overlay, 0.25, annotated_frame, 0.75, 0, annotated_frame)

        return {
            "detections": detections,
            "alerts": alerts,
            "annotated_frame": annotated_frame,
            "breach_detected": breach_detected
        }


# Global shared vision engine instance
_shared_engine: Optional[VisionEngine] = None

def _get_engine_instance() -> VisionEngine:
    global _shared_engine
    if _shared_engine is None:
        _shared_engine = VisionEngine(model_path="yolov8n.pt")
    return _shared_engine


async def run_vision_pipeline(
    source: Union[str, int],
    zones: Optional[List[Dict[str, Any]]] = None,
    enable_clahe: bool = False
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    High-performance, non-blocking asynchronous generator video analytics pipeline.
    
    1. Video Ingestion: Reads stream/file, loops video files continuously for offline testing.
    2. Pre-processing: Low-light CLAHE enhancement on L-channel in LAB space.
    3. Inference & ByteTrack Tracking: Target threat filtering & false alarm animal suppression.
    4. Spatial Math: Ray-casting point-in-polygon breach evaluation.
    5. Frame Annotation & Base64 Encoding: Renders semi-transparent zones & encoded JPEG telemetry.
    6. Non-blocking Concurrency: Offloads heavy OpenCV/YOLO inference to background threads.
    """
    engine = _get_engine_instance()
    if zones is None:
        zones = []

    is_file_source = isinstance(source, str) and (
        source.endswith((".mp4", ".avi", ".mkv", ".mov", ".flv")) or os.path.isfile(source)
    )

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        logger.error(f"Failed to open video source: {source}")

    prev_time = time.time()

    def _read_and_process_sync() -> Tuple[bool, Optional[Dict[str, Any]]]:
        nonlocal cap, prev_time
        if not cap.isOpened():
            cap.open(source)
            if not cap.isOpened():
                return False, None

        ret, frame = cap.read()
        if not ret or frame is None:
            if is_file_source:
                # Loop continuous video playback for testing
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()

            if not ret or frame is None:
                return False, None

        current_time = time.time()
        fps = 1.0 / (current_time - prev_time) if current_time > prev_time else 30.0
        prev_time = current_time

        # Run vision inference & spatial math
        result = engine.process_frame(frame, zones=zones, enable_clahe=enable_clahe)
        annotated_frame = result["annotated_frame"]

        # Encode frame to JPEG and Base64
        _, jpg_buf = cv2.imencode(".jpg", annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        b64_str = base64.b64encode(jpg_buf).decode("utf-8")

        telemetry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "fps": round(fps, 1),
            "frame_b64": f"data:image/jpeg;base64,{b64_str}",
            "alert_triggered": result["breach_detected"],
            "active_tracks_count": len(result["detections"]),
            "detections": result["detections"]
        }
        return True, telemetry

    try:
        while True:
            # Offload heavy CV & inference to thread executor to prevent event loop blocking
            success, telemetry = await asyncio.to_thread(_read_and_process_sync)

            if success and telemetry is not None:
                yield telemetry
            else:
                # Handle stream disconnection gracefully
                await asyncio.sleep(0.5)

            # Yield control back to event loop
            await asyncio.sleep(0.01)
    finally:
        if cap and cap.isOpened():
            cap.release()
