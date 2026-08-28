import os
import time
import base64
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, AsyncGenerator, Tuple
from collections import deque
import cv2
import numpy as np
from ultralytics import YOLO

from app.vision.spatial import is_point_in_polygon, calculate_bottom_center
from app.services.telegram import get_telegram_service

logger = logging.getLogger("RakshaVisionEngine")
logging.basicConfig(level=logging.INFO)

# Data, Snapshot & Video Storage Setup
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
SNAPSHOTS_DIR = os.path.join(DATA_DIR, "snapshots")
CLIPS_DIR = os.path.join(DATA_DIR, "clips")
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
os.makedirs(CLIPS_DIR, exist_ok=True)

# COCO Class Mappings & Threat Definitions
THREAT_CLASSES = {"person", "car", "motorcycle", "bus", "truck"}
BENIGN_ANIMALS = {"cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "bird"}


def generate_video_clip(frames: List[np.ndarray], output_path: str, fps: float = 15.0) -> Optional[str]:
    """
    Compiles a list of BGR image frames into a 5-second MP4 video clip.
    Returns the video file path if successful, None otherwise.
    """
    if not frames:
        return None

    try:
        height, width = frames[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        for f in frames:
            if f.shape[:2] != (height, width):
                f = cv2.resize(f, (width, height))
            out.write(f)
        out.release()
        logger.info(f"Successfully generated 5-second MP4 video clip: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to generate MP4 video clip: {e}")
        return None


def dispatch_telegram_alert_async(alert_data: Dict[str, Any]):
    """
    Dispatches high-priority Telegram alert asynchronously without blocking
    the computer vision inference loop or FastAPI event loop.
    """
    try:
        telegram_svc = get_telegram_service()
        if not telegram_svc.is_configured:
            return

        coro = telegram_svc.send_breach_alert(
            camera_id=alert_data.get("camera_id", 1),
            object_type=alert_data.get("object_type", "unknown"),
            confidence=alert_data.get("confidence", 0.0),
            timestamp=alert_data.get("timestamp", datetime.utcnow().isoformat()),
            zone_name=alert_data.get("zone_name"),
            video_path=alert_data.get("video_clip_path"),
            photo_path=alert_data.get("snapshot_path")
        )

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(coro)
        except RuntimeError:
            asyncio.run(coro)
    except Exception as exc:
        logger.error(f"Error dispatching async Telegram alert: {exc}")


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
        self.frame_buffers: Dict[int, deque] = {}

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

        # Store frame in rolling buffer for 5-second MP4 clip generation (approx 15 FPS * 5 sec = 75 frames max)
        if camera_id not in self.frame_buffers:
            self.frame_buffers[camera_id] = deque(maxlen=75)
        self.frame_buffers[camera_id].append(frame.copy())

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

                # Handle snapshot & 5-second MP4 video clip alert creation
                if is_breaching:
                    alert_key = (track_id, camera_id) if track_id is not None else (time.time(), camera_id)
                    if alert_key not in self.active_alert_ids:
                        self.active_alert_ids.add(alert_key)
                        ts_ms = int(time.time() * 1000)
                        timestamp_str = datetime.utcnow().isoformat()

                        snapshot_filename = f"incident_cam{camera_id}_{ts_ms}.jpg"
                        snapshot_path = os.path.join(SNAPSHOTS_DIR, snapshot_filename)
                        cv2.imwrite(snapshot_path, annotated_frame)

                        # Compile 5-second MP4 video clip from rolling frame buffer
                        video_filename = f"breach_cam{camera_id}_{ts_ms}.mp4"
                        video_path = os.path.join(CLIPS_DIR, video_filename)
                        buffered_frames = list(self.frame_buffers.get(camera_id, [frame]))
                        video_clip_path = generate_video_clip(buffered_frames, video_path)

                        zone_name = None
                        if zones:
                            for z in zones:
                                z_id = z.get("id")
                                if (z_id and z_id in breached_zone_ids) or breach_detected:
                                    zone_name = z.get("name")
                                    break

                        alert_data = {
                            "camera_id": camera_id,
                            "object_type": class_name,
                            "confidence": round(conf, 3),
                            "bbox": [round(c, 1) for c in xyxy],
                            "snapshot_path": snapshot_path,
                            "video_clip_path": video_clip_path,
                            "zone_name": zone_name,
                            "timestamp": timestamp_str
                        }
                        alerts.append(alert_data)

                        # Dispatch asynchronous, non-blocking Telegram alert
                        dispatch_telegram_alert_async(alert_data)

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
