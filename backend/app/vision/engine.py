import os
import time
import logging
import cv2
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from ultralytics import YOLO

from app.vision.spatial import is_bbox_in_polygon, get_bbox_bottom_center, do_line_segments_intersect

logger = logging.getLogger("RakshaVisionEngine")
logging.basicConfig(level=logging.INFO)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
SNAPSHOTS_DIR = os.path.join(DATA_DIR, "snapshots")
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

class VisionEngine:
    def __init__(self, model_path: str = "yolov8n.pt", confidence_threshold: float = 0.4):
        """
        Initializes OpenCV + YOLOv8 + ByteTrack object tracking engine.
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        logger.info(f"Initializing VisionEngine with model: {model_path}")
        # Initialize YOLOv8
        self.model = YOLO(model_path)
        self.track_history: Dict[int, List[tuple]] = {}  # track_id -> [(x, y), ...]
        self.active_alert_ids = set()  # set of track_ids currently alerted to prevent duplicate spam

    def process_frame(
        self,
        frame: np.ndarray,
        zones: List[Dict[str, Any]],
        camera_id: int = 1,
        alert_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Processes a single video frame, performs YOLOv8 detection & ByteTrack tracking,
        evaluates target coordinates against active security zones, and raises alert incidents.

        :param frame: BGR image frame from OpenCV
        :param zones: List of dicts representing active zones for this camera.
                      e.g. [{'id': 1, 'name': 'Zone A', 'polygon_coords': [[10,10],[100,10],[100,100],[10,100]], 'alert_type': 'intrusion'}]
        :param camera_id: ID of the camera source
        :param alert_callback: Callable function invoked when an intrusion/breach is detected
        :return: Dict containing processed detections, track items, annotated frame, and alerts
        """
        if frame is None or frame.size == 0:
            return {"detections": [], "alerts": [], "annotated_frame": frame}

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

        if not results or len(results) == 0:
            return {"detections": [], "alerts": [], "annotated_frame": annotated_frame}

        res = results[0]
        boxes = res.boxes

        if boxes is not None and len(boxes) > 0:
            for box in boxes:
                # Extract coordinates
                xyxy = box.xyxy[0].cpu().numpy().tolist()  # [x1, y1, x2, y2]
                conf = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy())
                class_name = self.model.names.get(cls_id, f"class_{cls_id}")

                # Extract track_id if available from ByteTrack
                track_id = int(box.id[0].cpu().numpy()) if box.id is not None else None

                det = {
                    "track_id": track_id,
                    "class_name": class_name,
                    "confidence": round(conf, 3),
                    "bbox": [round(c, 1) for c in xyxy]
                }
                detections.append(det)

                # Draw bounding box on annotated frame
                x1, y1, x2, y2 = [int(c) for c in xyxy]
                color = (0, 255, 0)  # Green by default

                # Check spatial position against active zones
                is_intrusion = False
                triggered_zone = None

                for z in zones:
                    poly = z.get("polygon_coords", [])
                    if len(poly) >= 3:
                        if is_bbox_in_polygon(xyxy, poly, ref_point="bottom_center"):
                            is_intrusion = True
                            triggered_zone = z
                            color = (0, 0, 255)  # Red for perimeter breach
                            break

                # Draw bounding box label
                label = f"{class_name}"
                if track_id is not None:
                    label += f" #{track_id}"
                label += f" {conf:.2f}"
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(annotated_frame, label, (x1, max(y1 - 10, 15)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                # Handle Alert Incident Creation & Snapshot Saving
                if is_intrusion and triggered_zone is not None:
                    alert_key = (track_id, triggered_zone["id"]) if track_id is not None else (time.time(), triggered_zone["id"])
                    
                    if alert_key not in self.active_alert_ids:
                        self.active_alert_ids.add(alert_key)
                        
                        # Save snapshot image
                        snapshot_filename = f"incident_cam{camera_id}_{int(time.time()*1000)}.jpg"
                        snapshot_path = os.path.join(SNAPSHOTS_DIR, snapshot_filename)
                        cv2.imwrite(snapshot_path, annotated_frame)

                        alert_data = {
                            "camera_id": camera_id,
                            "zone_id": triggered_zone["id"],
                            "zone_name": triggered_zone.get("name", "Unknown Zone"),
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
                                logger.error(f"Error in alert callback: {e}")

        # Draw Zone Polygons on annotated frame
        for z in zones:
            poly = z.get("polygon_coords", [])
            if len(poly) >= 3:
                pts = np.array(poly, np.int32).reshape((-1, 1, 2))
                cv2.polylines(annotated_frame, [pts], isClosed=True, color=(255, 255, 0), thickness=2)
                # Zone name label
                cx, cy = int(np.mean([p[0] for p in poly])), int(np.mean([p[1] for p in poly]))
                cv2.putText(annotated_frame, z.get("name", "Zone"), (cx, cy),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

        return {
            "detections": detections,
            "alerts": alerts,
            "annotated_frame": annotated_frame
        }
