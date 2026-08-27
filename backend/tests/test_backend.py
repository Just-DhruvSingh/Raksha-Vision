import os
import sys
import numpy as np
import pytest
from fastapi.testclient import TestClient

# Ensure app package is on python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import engine, Base, SessionLocal
from app import models
from app.vision.spatial import is_point_in_polygon, is_bbox_in_polygon, do_line_segments_intersect
from app.vision.engine import VisionEngine

# Create test database tables
Base.metadata.create_all(bind=engine)
client = TestClient(app)

def test_spatial_ray_casting():
    # Square polygon from (10, 10) to (100, 100)
    poly = [[10.0, 10.0], [100.0, 10.0], [100.0, 10.00], [10.0, 100.0]]
    # Correct convex square
    poly = [[10.0, 10.0], [100.0, 10.0], [100.0, 100.0], [10.0, 100.0]]

    # Test point inside
    assert is_point_in_polygon((50.0, 50.0), poly) is True
    # Test point outside
    assert is_point_in_polygon((150.0, 50.0), poly) is False
    assert is_point_in_polygon((50.0, 150.0), poly) is False
    assert is_point_in_polygon((0.0, 0.0), poly) is False

    # Bounding box test [x1, y1, x2, y2] -> bottom center is (50, 80)
    bbox_inside = [40.0, 20.0, 60.0, 80.0]
    assert is_bbox_in_polygon(bbox_inside, poly, ref_point="bottom_center") is True

    # Bounding box outside -> bottom center is (150, 80)
    bbox_outside = [140.0, 20.0, 160.0, 80.0]
    assert is_bbox_in_polygon(bbox_outside, poly, ref_point="bottom_center") is False

def test_line_intersection():
    # Vertical line segment crossing horizontal line segment
    p1, p2 = (50.0, 0.0), (50.0, 100.0)
    q1, q2 = (0.0, 50.0), (100.0, 50.0)
    assert do_line_segments_intersect(p1, p2, q1, q2) is True

    # Non-intersecting parallel lines
    r1, r2 = (0.0, 60.0), (100.0, 60.0)
    assert do_line_segments_intersect(q1, q2, r1, r2) is False

def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["database"] == "SQLite (WAL Mode)"

def test_camera_crud_endpoints():
    # 1. Create camera
    payload = {
        "name": "North Wall PTZ",
        "rtsp_url": "rtsp://192.168.1.101:554/live",
        "location": "North Fence Line",
        "is_active": True
    }
    create_res = client.post("/api/cameras", json=payload)
    assert create_res.status_code == 201
    cam = create_res.json()
    cam_id = cam["id"]
    assert cam["name"] == payload["name"]

    # 2. List cameras
    list_res = client.get("/api/cameras")
    assert list_res.status_code == 200
    cams = list_res.json()
    assert len(cams) >= 1

    # 3. Get camera details
    get_res = client.get(f"/api/cameras/{cam_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == cam_id

    # 4. Update camera
    update_res = client.put(f"/api/cameras/{cam_id}", json={"name": "North Perimeter Main"})
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "North Perimeter Main"

    # 5. Delete camera
    del_res = client.delete(f"/api/cameras/{cam_id}")
    assert del_res.status_code == 204

def test_zone_crud_endpoints():
    # Create camera first
    cam_res = client.post("/api/cameras", json={
        "name": "East Gate",
        "rtsp_url": "rtsp://192.168.1.102:554/live"
    })
    cam_id = cam_res.json()["id"]

    # 1. Create zone
    zone_payload = {
        "camera_id": cam_id,
        "name": "Restricted Sector 1",
        "polygon_coords": [[100.0, 100.0], [500.0, 100.0], [500.0, 500.0], [100.0, 500.0]],
        "alert_type": "intrusion",
        "is_active": True
    }
    zone_res = client.post("/api/zones", json=zone_payload)
    assert zone_res.status_code == 201
    zone = zone_res.json()
    zone_id = zone["id"]

    # 2. List zones by camera
    list_res = client.get(f"/api/zones?camera_id={cam_id}")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1

    # 3. Delete zone
    del_res = client.delete(f"/api/zones/{zone_id}")
    assert del_res.status_code == 204

def test_vision_engine_spatial_processing():
    # Create a synthetic black frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    zones = [{
        "id": 1,
        "name": "Test Intrusion Zone",
        "polygon_coords": [[50.0, 50.0], [300.0, 50.0], [300.0, 300.0], [50.0, 300.0]],
        "alert_type": "intrusion"
    }]

    alerts_triggered = []
    def on_alert(alert):
        alerts_triggered.append(alert)

    engine_inst = VisionEngine(model_path="yolov8n.pt")
    output = engine_inst.process_frame(frame, zones=zones, camera_id=1, alert_callback=on_alert)

    assert "detections" in output
    assert "alerts" in output
    assert "annotated_frame" in output
    assert output["annotated_frame"].shape == (480, 640, 3)
