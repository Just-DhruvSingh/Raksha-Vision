import os
import re
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
from app.api.notifications import send_telegram_alert, send_telegram_photo, send_telegram_video

logger = logging.getLogger("RakshaVisionEngine")
logging.basicConfig(level=logging.INFO)

# Data, Snapshot & Incident Media Storage
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
SNAPSHOTS_DIR = os.path.join(DATA_DIR, "snapshots")
INCIDENT_MEDIA_DIR = os.path.join(DATA_DIR, "incident_media")
SAMPLE_VIDEOS_DIR = os.path.join(DATA_DIR, "sample_videos")

os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
os.makedirs(INCIDENT_MEDIA_DIR, exist_ok=True)
os.makedirs(SAMPLE_VIDEOS_DIR, exist_ok=True)

# COCO Class Mappings & Threat Definitions
THREAT_CLASSES = {"person", "car", "motorcycle", "bus", "truck"}
VEHICLE_CLASSES = {"car", "motorcycle", "bus", "truck"}
BENIGN_ANIMALS = {"cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "bird"}

# Lazy-loaded EasyOCR Reader singleton
_ocr_reader = None

def get_ocr_reader():
    """Lazily initializes the offline EasyOCR reader for ANPR license plate recognition."""
    global _ocr_reader
    if _ocr_reader is None:
        try:
            import easyocr
            logger.info("Initializing offline EasyOCR ANPR Reader (GPU=False)...")
            _ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            logger.info("EasyOCR ANPR Reader successfully initialized.")
        except Exception as e:
            logger.warning(f"EasyOCR initialization deferred or failed: {e}")
            _ocr_reader = False
    return _ocr_reader if _ocr_reader is not False else None


def clean_plate_text(text: str) -> Optional[str]:
    """Cleans and standardizes extracted license plate string."""
    if not text:
        return None
    # Remove non-alphanumeric characters, convert to uppercase
    cleaned = re.sub(r'[^A-Za-z0-9]', '', text).upper()
    if 4 <= len(cleaned) <= 12:
        return cleaned
    return None


def generate_video_clip(frames: List[np.ndarray], output_path: str, fps: float = 15.0) -> Optional[str]:
    """
    Compiles a list of BGR image frames into a 5-second MP4 video clip.
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
        logger.info(f"Generated 5-second MP4 breach clip: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to generate MP4 clip: {e}")
        return None


def fire_async_telegram_task(coro):
    """Schedules a coroutine on the running asyncio event loop without blocking."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        # Fallback if called outside active event loop
        try:
            asyncio.run(coro)
        except Exception as e:
            logger.error(f"Failed to run async Telegram task: {e}")


def apply_clahe_lowlight(frame: np.ndarray, clip_limit: float = 2.0, tile_grid_size: Tuple[int, int] = (8, 8)) -> np.ndarray:
    """
    Applies CLAHE (Contrast Limited Adaptive Histogram Equalization) on L-channel 
    in LAB color space to enhance low-light and thermal surveillance feeds.
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
        """Initializes YOLOv8 + ByteTrack + ANPR Vision Engine."""
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        logger.info(f"Initializing VisionEngine with YOLO model: {model_path}")
        self.model = YOLO(model_path)
        self.active_alert_ids = set()
        self.active_plate_alerts = set()
        self.frame_buffers: Dict[Union[int, str], deque] = {}
        self.plate_cache: Dict[int, str] = {}  # track_id -> license_plate
        self.frame_count = 0

    def process_frame(
        self,
        frame: np.ndarray,
        zones: Optional[List[Dict[str, Any]]] = None,
        camera_id: Union[int, str] = 1,
        alert_callback: Optional[Any] = None,
        enable_clahe: bool = False
    ) -> Dict[str, Any]:
        """
        Processes a single BGR frame:
        1. Low-light CLAHE enhancement (optional).
        2. YOLOv8 + ByteTrack object tracking.
        3. Animal false alarm suppression.
        4. Offline ANPR for vehicles on every 5th frame.
        5. Spatial Ray-Casting polygon breach evaluation.
        6. HUD annotations & async Telegram triggers.
        """
        if frame is None or frame.size == 0:
            return {"detections": [], "alerts": [], "annotated_frame": frame, "breach_detected": False}

        self.frame_count += 1

        # Store rolling 5-second frame buffer (15 FPS * 5s = 75 frames)
        if camera_id not in self.frame_buffers:
            self.frame_buffers[camera_id] = deque(maxlen=75)
        self.frame_buffers[camera_id].append(frame.copy())

        if enable_clahe:
            frame = apply_clahe_lowlight(frame)

        if zones is None:
            zones = []

        # YOLOv8 ByteTrack multi-object tracking
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
        breached_zone_ids = set()

        if not results or len(results) == 0:
            return {
                "detections": [],
                "alerts": [],
                "annotated_frame": annotated_frame,
                "breach_detected": False
            }

        res = results[0]
        boxes = res.boxes
        h, w = frame.shape[:2]
        ocr_reader = get_ocr_reader() if self.frame_count % 5 == 0 else None

        if boxes is not None and len(boxes) > 0:
            for box in boxes:
                xyxy = box.xyxy[0].cpu().numpy().tolist()  # [x1, y1, x2, y2]
                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                class_name = self.model.names.get(cls_id, f"class_{cls_id}").lower()

                # 1. Benign Wildlife Suppression
                if class_name in BENIGN_ANIMALS:
                    continue

                track_id = int(box.id[0].cpu().numpy()) if box.id is not None else -1
                x1, y1, x2, y2 = [max(0, int(c)) for c in xyxy]
                x2, y2 = min(w, x2), min(h, y2)

                # 2. Offline ANPR on Vehicle Bounding Boxes (Every 5th frame)
                plate_text = self.plate_cache.get(track_id)
                if class_name in VEHICLE_CLASSES:
                    if self.frame_count % 5 == 0 and ocr_reader and (x2 - x1 > 30 and y2 - y1 > 30):
                        try:
                            # Crop vehicle ROI
                            crop = frame[y1:y2, x1:x2]
                            ocr_res = ocr_reader.readtext(crop)
                            for item in ocr_res:
                                cand_text = clean_plate_text(item[1])
                                if cand_text:
                                    plate_text = cand_text
                                    self.plate_cache[track_id] = plate_text
                                    
                                    # Trigger ANPR Telegram alert on newly recognized plate
                                    plate_alert_key = (camera_id, track_id, plate_text)
                                    if plate_alert_key not in self.active_plate_alerts:
                                        self.active_plate_alerts.add(plate_alert_key)
                                        anpr_msg = (
                                            "🚘 <b>ANPR LICENSE PLATE RECOGNIZED</b>\n\n"
                                            f"<b>Camera:</b> CAM-{camera_id}\n"
                                            f"<b>License Plate:</b> <code>{plate_text}</code>\n"
                                            f"<b>Vehicle Type:</b> {class_name.upper()}\n"
                                            f"<b>Confidence:</b> {conf*100:.1f}%\n"
                                            f"<b>Time:</b> {datetime.utcnow().strftime('%H:%M:%S UTC')}"
                                        )
                                        fire_async_telegram_task(send_telegram_alert(anpr_msg))
                                    break
                        except Exception as ocr_err:
                            logger.debug(f"OCR scan failed for track {track_id}: {ocr_err}")

                # 3. Bottom-Center Contact Point & Spatial Polygon Ray-Casting
                bottom_center = calculate_bottom_center(xyxy)
                is_breaching = False
                zone_name = None

                if class_name in THREAT_CLASSES:
                    for z in zones:
                        poly = z.get("polygon_coords") or z.get("polygon") or []
                        if len(poly) >= 3:
                            if is_point_in_polygon(bottom_center, poly):
                                is_breaching = True
                                breach_detected = True
                                zone_name = z.get("name", "Restricted Zone")
                                if "id" in z:
                                    breached_zone_ids.add(z["id"])
                                break

                # Construct detection telemetry
                det = {
                    "track_id": track_id,
                    "class_label": class_name,
                    "confidence": round(conf, 3),
                    "bbox": [round(c, 1) for c in xyxy],
                    "is_breaching": is_breaching,
                    "license_plate": plate_text
                }
                detections.append(det)

                # 4. HUD Annotations
                color = (0, 0, 255) if is_breaching else (0, 255, 0)
                label = f"{class_name}"
                if track_id != -1:
                    label += f" #{track_id}"
                if plate_text:
                    label += f" [{plate_text}]"
                label += f" {conf:.2f}"
                if is_breaching:
                    label += " [BREACH]"

                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(annotated_frame, label, (x1, max(y1 - 8, 15)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                # 5. Handle Intrusion Breach Snapshot & Video Clip Creation
                if is_breaching:
                    alert_key = (camera_id, track_id) if track_id != -1 else (camera_id, time.time())
                    if alert_key not in self.active_alert_ids:
                        self.active_alert_ids.add(alert_key)
                        ts_ms = int(time.time() * 1000)
                        timestamp_str = datetime.utcnow().isoformat()

                        # Save snapshot
                        snapshot_filename = f"breach_cam{camera_id}_{ts_ms}.jpg"
                        snapshot_path = os.path.join(SNAPSHOTS_DIR, snapshot_filename)
                        cv2.imwrite(snapshot_path, annotated_frame)

                        # Compile 5-second MP4 breach clip
                        video_filename = f"clip_cam{camera_id}_{ts_ms}.mp4"
                        video_clip_path = os.path.join(INCIDENT_MEDIA_DIR, video_filename)
                        buffered_frames = list(self.frame_buffers.get(camera_id, [frame]))
                        video_path = generate_video_clip(buffered_frames, video_clip_path)

                        alert_data = {
                            "camera_id": camera_id,
                            "object_type": class_name,
                            "confidence": round(conf, 3),
                            "bbox": [round(c, 1) for c in xyxy],
                            "license_plate": plate_text,
                            "snapshot_path": snapshot_path,
                            "video_clip_path": video_path or snapshot_path,
                            "zone_name": zone_name,
                            "timestamp": timestamp_str
                        }
                        alerts.append(alert_data)

                        # Trigger Instant Non-Blocking Telegram Alert
                        tele_caption = (
                            "🚨 <b>PERIMETER BREACH INTRUSION ALERT</b> 🚨\n\n"
                            f"<b>Camera:</b> CAM-{camera_id}\n"
                            f"<b>Zone:</b> {zone_name or 'Restricted Sector'}\n"
                            f"<b>Threat:</b> {class_name.upper()}\n"
                            + (f"<b>License Plate:</b> <code>{plate_text}</code>\n" if plate_text else "")
                            + f"<b>Confidence:</b> {conf * 100:.1f}%\n"
                            f"<b>Time:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                            "⚠️ <i>Action Required: Security team dispatched.</i>"
                        )
                        if video_path and os.path.exists(video_path):
                            fire_async_telegram_task(send_telegram_video(video_path, caption=tele_caption))
                        else:
                            fire_async_telegram_task(send_telegram_photo(snapshot_path, caption=tele_caption))

                        if alert_callback:
                            try:
                                alert_callback(alert_data)
                            except Exception as cb_err:
                                logger.error(f"Alert callback error: {cb_err}")

        # 6. Draw Polygonal Defense Zones
        if zones:
            overlay = annotated_frame.copy()
            for z in zones:
                poly = z.get("polygon_coords") or z.get("polygon") or []
                if len(poly) >= 3:
                    pts = np.array(poly, np.int32).reshape((-1, 1, 2))
                    zone_id = z.get("id")
                    is_zone_breached = zone_id in breached_zone_ids if zone_id else breach_detected

                    fill_color = (0, 0, 220) if is_zone_breached else (0, 220, 255)
                    line_color = (0, 0, 255) if is_zone_breached else (0, 255, 255)

                    cv2.fillPoly(overlay, [pts], fill_color)
                    cv2.polylines(annotated_frame, [pts], isClosed=True, color=line_color, thickness=2)

                    cx = int(np.mean([p[0] for p in poly]))
                    cy = int(np.mean([p[1] for p in poly]))
                    cv2.putText(annotated_frame, z.get("name", "DEFENSE ZONE"), (cx - 40, cy),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

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
    source: Union[str, int] = 0,
    zones: Optional[List[Dict[str, Any]]] = None,
    enable_clahe: bool = False,
    camera_id: Union[int, str] = 1
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Asynchronous video analytics pipeline supporting:
    - Live Webcams (source=0, '0', 'cam_live')
    - Offline .mp4/.avi CCTV Video Files (with continuous playback loop)
    - RTSP Stream URLs
    """
    engine = _get_engine_instance()
    if zones is None:
        zones = []

    # Check if source is webcam or file
    is_webcam = (
        source == 0 or source == "0" or str(source).lower() in ["cam_live", "webcam", "live"]
    )
    
    video_source: Union[int, str] = 0 if is_webcam else source

    # Open VideoCapture
    if is_webcam:
        # On Windows, try cv2.CAP_DSHOW for fast camera opening
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(0)
    else:
        cap = cv2.VideoCapture(video_source)

    if not cap.isOpened():
        logger.warning(f"Unable to open video source: {video_source}. Falling back to default webcam (0)...")
        cap = cv2.VideoCapture(0)

    prev_time = time.time()

    def _read_and_process_sync() -> Tuple[bool, Optional[Dict[str, Any]]]:
        nonlocal cap, prev_time
        if not cap.isOpened():
            cap.open(video_source)
            if not cap.isOpened():
                return False, None

        ret, frame = cap.read()
        if not ret or frame is None:
            if not is_webcam:
                # Loop video file continuously for uninterrupted demonstration
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()

            if not ret or frame is None:
                return False, None

        current_time = time.time()
        fps = 1.0 / (current_time - prev_time) if current_time > prev_time else 30.0
        prev_time = current_time

        # Process frame through YOLOv8 + ByteTrack + ANPR + Spatial Ray-Casting
        result = engine.process_frame(
            frame,
            zones=zones,
            camera_id=camera_id,
            enable_clahe=enable_clahe
        )
        annotated_frame = result["annotated_frame"]

        # Encode frame to JPEG Base64
        _, jpg_buf = cv2.imencode(".jpg", annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        b64_str = base64.b64encode(jpg_buf).decode("utf-8")

        telemetry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "camera_id": camera_id,
            "fps": round(fps, 1),
            "frame_b64": f"data:image/jpeg;base64,{b64_str}",
            "threat_level": "CRITICAL" if result["breach_detected"] else "NORMAL",
            "alert_triggered": result["breach_detected"],
            "active_tracks_count": len(result["detections"]),
            "detections": result["detections"],
            "alerts": result["alerts"]
        }
        return True, telemetry

    try:
        while True:
            # Offload heavy CV processing to worker thread to prevent event loop starvation
            success, telemetry = await asyncio.to_thread(_read_and_process_sync)

            if success and telemetry is not None:
                yield telemetry
            else:
                await asyncio.sleep(0.1)

            await asyncio.sleep(0.01)
    finally:
        if cap and cap.isOpened():
            cap.release()
