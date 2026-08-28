# 🛡️ RakshaVision AI
> **Edge-Native Perimeter Defense & Intrusion Detection System**

RakshaVision AI is a real-time computer vision and spatial intelligence platform developed for **Smart India Hackathon (SIH Problem Statement 26187)**. It connects **YOLOv8 + ByteTrack object tracking**, **Ray-Casting spatial polygon math**, **CLAHE low-light enhancement**, **real-time WebSocket telemetry**, and an interactive **React + Vite dashboard**.

---

## 📁 Repository Structure

```text
RakshaVision-AI/
├── .gitignore                         # Multi-tier ignore rules
├── README.md                          # Architecture & quick start documentation
├── start_demo.bat                     # 🪟 Windows 1-Click Startup Automation
├── start_demo.sh                      # 🐧 macOS / Linux 1-Click Startup Automation
├── backend/
│   ├── .env                           # Local config (SQLite WAL, Telegram, Ports)
│   ├── .env.example                   # Config template
│   ├── requirements.txt               # Locked backend dependencies
│   ├── data/
│   │   ├── rakshavision.db            # SQLite WAL database
│   │   ├── incident_media/            # Stored 5s MP4 breach clips & thumbnails
│   │   └── sample_videos/             # Offline CCTV test footage
│   └── app/
│       ├── __init__.py
│       ├── main.py                    # FastAPI entrypoint, Static Mounts, WebSockets
│       ├── database.py                # SQLite engine + WAL mode configuration
│       ├── models.py                  # SQLAlchemy Models (Camera, Zone, Incident)
│       ├── schemas.py                 # Pydantic validation schemas
│       ├── api/
│       │   ├── camera_routes.py       # Camera deployment REST APIs
│       │   ├── zone_routes.py         # Polygon Zone REST APIs
│       │   ├── incident_routes.py     # Incident query & status update endpoints
│       │   ├── alert_routes.py        # Real-time alert feed & acknowledge endpoints
│       │   ├── analytics_routes.py    # Detection analytics & activity endpoints
│       │   └── extra_routes.py        # Siren controls, settings & Telegram dispatch
│       ├── services/
│       │   └── telegram.py            # Async Telegram Bot Service (httpx)
│       └── vision/
│           ├── spatial.py             # Ray-Casting & contact point math
│           └── engine.py              # YOLOv8 + ByteTrack + CLAHE + Video pipeline
└── frontend/
    ├── .env                           # VITE_API_BASE_URL & VITE_WS_BASE_URL
    ├── .env.example
    ├── package.json                   # React 19, Lucide, React Router
    ├── vite.config.js                 # Dev server with proxy to http://127.0.0.1:8000
    ├── index.html                     # HTML5 template
    ├── App.jsx                        # React Router configuration
    ├── dashboard.jsx                  # Surveillance Dashboard Overview
    ├── liveMonitoring.jsx             # Live CCTV Matrix
    ├── Cameras.jsx                    # Connected Cameras View
    ├── Incidents.jsx                  # Security Incidents Log
    ├── Alerts.jsx                     # Security Alerts Feed
    ├── Analytics.jsx                  # Threat Analytics
    └── Settings.jsx                   # System Preferences
```

---

## ⚡ 1-Click Demo Launch

### 🪟 Windows Users
Double-click **`start_demo.bat`** (or run in CMD/PowerShell):
```cmd
start_demo.bat
```

### 🐧 Linux / macOS Users
```bash
chmod +x start_demo.sh
./start_demo.sh
```

---

## 🛠️ Manual Step-by-Step Setup

### 1. Start Backend (FastAPI + YOLOv8 + SQLite)
```bash
cd backend
python -m venv .venv

# On Windows:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
* Interactive Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
* Health Check: [http://localhost:8000/health](http://localhost:8000/health)
* WebSocket Endpoint: `ws://localhost:8000/ws/live`

### 2. Start Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
* Command Center Dashboard: [http://localhost:5173/](http://localhost:5173/)

---

## 📄 License
All rights reserved for this idea 
