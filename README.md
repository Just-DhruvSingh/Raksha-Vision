# 🛡️ RakshaVision AI (SIH26187)
> **Edge-Native Perimeter Defense & Intrusion Detection System**

RakshaVision AI is a high-performance, real-time computer vision and spatial analytics backend built for edge perimeter security. It uses YOLOv8 object detection, ByteTrack multi-object tracking, and ray-casting spatial math to detect perimeter breaches, suppress false alarms, and broadcast instant WebSocket security alerts.

---

## 🛠️ Key Features

- **🎯 AI Threat Detection & Tracking**: Powered by YOLOv8 and ByteTrack to track targets across frames seamlessly.
- **📐 Ray-Casting Polygon Zones**: Define custom multi-vertex restricted spatial zones; automatically calculates feet/contact points to detect true ground breaches.
- **🐾 False Alarm Animal Suppression**: Automatically filters out benign animals (cats, dogs, birds, cows, etc.) to eliminate false alarm noise.
- **🌙 Low-Light CLAHE Enhancement**: Contrast Limited Adaptive Histogram Equalization in LAB color space for enhanced night-vision/thermal contrast.
- **⚡ Real-Time WebSocket Alerts**: Low-latency event streaming (`/ws/alerts`) for immediate dashboard notification.
- **📸 Automatic Snapshot Management**: Auto-captures and stores incident snapshots with spatial boundary annotations.
- **📚 Interactive OpenAPI Docs**: Built-in Swagger UI for testing all REST endpoints effortlessly.

---

## 📁 Project Structure

```text
Raksha-Vision/
├── README.md                  # Project Documentation & Setup Guide
├── .gitignore                 # Git ignore rules
└── backend/
    ├── app/
    │   ├── main.py            # FastAPI Application Entrypoint & WebSockets
    │   ├── database.py        # SQLAlchemy SQLite (WAL mode) Engine Setup
    │   ├── models.py          # Database ORM Schema (Cameras, Zones, Incidents)
    │   ├── schemas.py         # Pydantic Request/Response Data Validation
    │   ├── api/
    │   │   ├── camera_routes.py # Camera Configuration REST Endpoints
    │   │   └── zone_routes.py   # Polygon Zone REST Endpoints
    │   └── vision/
    │       ├── engine.py      # Core CV Pipeline (YOLOv8, ByteTrack, CLAHE, Snapshots)
    │       └── spatial.py     # Ray-Casting Point-in-Polygon Mathematics
    ├── data/                  # Local SQLite DB & Incident Snapshot Storage
    ├── requirements.txt       # Python Project Dependencies
    └── tests/                 # Unit & Integration Tests
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python**: `3.10` or higher
- **Git**: Installed on your system

---

### 1. Clone the Repository
```bash
git clone https://github.com/Just-DhruvSingh/Raksha-Vision.git
cd Raksha-Vision/backend
```

---

### 2. Set Up Virtual Environment (`.venv`)

#### Windows (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

### 4. Run the Development Server
```bash
uvicorn app.main:app --reload --port 8000
```

---

### 5. Access the API & Documentation
Open your browser and navigate to:
* 🌐 **Root Endpoint**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* 📖 **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* 🏥 **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 🤝 Contributing & Collaboration

1. **Pull the latest changes** before editing:
   ```bash
   git pull origin main
   ```
2. Make your edits or add new features.
3. **Commit & Push**:
   ```bash
   git add .
   git commit -m "feat: describe your change"
   git push origin main
   ```

---

## 📄 License
This project is developed for **Smart India Hackathon (SIH26187)**. All rights reserved.
