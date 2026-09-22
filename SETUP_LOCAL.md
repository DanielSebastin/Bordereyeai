# Local Setup Guide - SIH Border Surveillance System

## Prerequisites
- ✅ Python 3.13.7 (Installed)
- ✅ Node.js v24.11.1 (Installed)
- ✅ npm 11.6.2 (Installed)

## Quick Setup (Run these commands)

### 1. Backend Setup

```powershell
# Navigate to project root
cd "d:\IVBAP\sih_border_survelliance"

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install Python dependencies
pip install -r requirements.txt

# Initialize database and seed test data
python -c "from backend.app.database.db_session import init_db; init_db()"

# Start backend server
cd backend
python -m app.main
# OR using uvicorn directly:
# uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will run on: **http://localhost:8000**

### 2. Frontend Setup (Separate Terminal)

```powershell
# Navigate to frontend folder
cd "d:\IVBAP\sih_border_survelliance\frontend"

# Install Node dependencies
npm install

# Start Next.js development server
npm run dev
```

Frontend will run on: **http://localhost:3000**

---

## Environment Variables

The `.env` file is already configured with:
```
GROQ_API_KEY=your_groq_api_key_here
LLM_PROVIDER=groq
DEVICE=cpu
```

---

## Video Files
The following video files are already present:
- `cam1.mp4` (10.6 MB) - Human detection
- `cam2.mp4` (8.5 MB) - Vehicle ANPR
- `cam3.mp4` (10.6 MB) - Low-light enhancement
- `cam4.mp4` (3.0 MB) - Virtual fence
- `cam5.mp4` (2.7 MB) - Crowd surveillance

These will be auto-loaded by the backend pipelines.

---

## Access Points After Setup

1. **Frontend Dashboard**: http://localhost:3000
2. **Live Monitoring**: http://localhost:3000/live-monitoring
3. **AI Search (NL Query)**: http://localhost:3000/ai-search
4. **Backend API Docs**: http://localhost:8000/docs
5. **Backend Health**: http://localhost:8000/health
6. **WebSocket Analytics**: ws://localhost:8000/ws/analytics

---

## Expected AI Features

### ✅ Working Features:
1. **Natural Language Query** (Feature 12) - Already configured with Groq API
2. **Multi-Camera Re-ID** (Feature 13) - Person tracking across cameras
3. **Human Detection** - CAM-01 with YOLO11
4. **Vehicle ANPR** - CAM-02 with license plate recognition
5. **Virtual Fence** - CAM-04 with intrusion detection
6. **Facial Recognition** - CAM-06 with webcam
7. **Audio Intelligence** - Features 17-18 (acoustic detection)

### 🎯 Real-Time Detection:
Once running, you'll see:
- Bounding boxes on people/vehicles
- Tracking IDs
- Confidence scores
- ANPR license plates
- Virtual fence violations
- Cross-camera Re-ID tracking

---

## Troubleshooting

### If Python packages fail to install:
```powershell
# Try upgrading pip first
python -m pip install --upgrade pip

# Install packages one by one if needed
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install ultralytics
pip install -r requirements.txt
```

### If YOLO model doesn't load:
The system will download `yolo11n.pt` automatically on first run. Make sure you have internet access.

### If frontend fails to start:
```powershell
# Clear npm cache
npm cache clean --force

# Remove node_modules and reinstall
Remove-Item -Recurse -Force node_modules
npm install
```

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                        │
│              http://localhost:3000                           │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │Live Monitor │  │  AI Search   │  │  Dashboard   │      │
│  └─────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST API + WebSocket
┌──────────────────────▼──────────────────────────────────────┐
│                Backend (FastAPI + Python)                    │
│              http://localhost:8000                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Vision AI Pipelines (YOLO + ByteTrack + ANPR)       │  │
│  │  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐         │  │
│  │  │CAM1│ │CAM2│ │CAM3│ │CAM4│ │CAM5│ │CAM6│         │  │
│  │  └────┘ └────┘ └────┘ └────┘ └────┘ └────┘         │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  NL Query Engine (Feature 12) - Groq LLM            │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Re-ID Engine (Feature 13) - Cross-camera Tracking  │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Audio Intelligence (Features 17-18)                 │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
            SQLite Database (surveillance.db)
            ChromaDB Vector Store
```

---

## Notes

- The system runs entirely on CPU (no GPU required)
- YOLO11n model will auto-download (~6 MB)
- All video processing happens in real-time
- WebSocket streams provide live detection updates
- Natural Language Query uses Groq's Llama 3.3 70B model
