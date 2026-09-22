# ✅ LOCAL SETUP COMPLETE!

## Setup Status

### ✅ Backend (Python)
- Virtual environment created: `venv/`
- All dependencies installed successfully
- Database ready: `surveillance.db`
- Video files present: cam1-5.mp4
- Environment configured: `.env` with Groq API key

### ✅ Frontend (Next.js)
- Node modules installed: `frontend/node_modules/`
- 612 packages installed
- Ready to run on port 3000

---

## 🚀 How to Start

### Option 1: Using PowerShell Scripts (Easiest)

**Open 2 separate PowerShell windows:**

**Window 1 - Backend:**
```powershell
cd "d:\IVBAP\sih_border_survelliance"
.\START_BACKEND.ps1
```

**Window 2 - Frontend:**
```powershell
cd "d:\IVBAP\sih_border_survelliance"
.\START_FRONTEND.ps1
```

### Option 2: Manual Commands

**Terminal 1 - Backend:**
```powershell
cd "d:\IVBAP\sih_border_survelliance"
.\venv\Scripts\Activate.ps1
cd backend
python -m app.main
```

**Terminal 2 - Frontend:**
```powershell
cd "d:\IVBAP\sih_border_survelliance\frontend"
npm run dev
```

---

## 🎯 Access Points

Once both servers are running:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend Dashboard** | http://localhost:3000 | Main web interface |
| **Live Monitoring** | http://localhost:3000/live-monitoring | Real-time camera feeds with AI detections |
| **AI Search** | http://localhost:3000/ai-search | Natural language query interface |
| **Backend API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **Backend Health** | http://localhost:8000/health | System health status |
| **WebSocket Analytics** | ws://localhost:8000/ws/analytics | Real-time detection stream |

---

## 🤖 AI Features Available

### Real-Time Vision AI (Auto-Started)
1. **CAM-01**: Human Detection with YOLO11 + ByteTrack
2. **CAM-02**: Vehicle ANPR (License Plate Recognition)
3. **CAM-03**: Low-Light Night Vision Enhancement
4. **CAM-04**: Virtual Fence Intrusion Detection
5. **CAM-05**: Crowd Surveillance & Acoustic Alerts
6. **CAM-06**: Facial Recognition (Webcam)

### Intelligent Query Engine
- **Natural Language Search**: Ask questions like "show me all people detected in the last hour"
- **Cross-Camera Re-ID**: Track individuals across multiple cameras
- **Trajectory Reconstruction**: See movement paths across camera zones

### Audio Intelligence
- Acoustic Event Detection
- Drone Sentry
- Threat Detection

---

## 📹 Video Sources

The system uses these pre-loaded video files:
- `cam1.mp4` (10.6 MB) - Pedestrian area
- `cam2.mp4` (8.5 MB) - Vehicle traffic
- `cam3.mp4` (10.6 MB) - Low-light scene
- `cam4.mp4` (3.0 MB) - Perimeter fence
- `cam5.mp4` (2.7 MB) - Crowd monitoring

---

## 🔧 Troubleshooting

### Backend won't start
```powershell
# Make sure you're in the right directory
cd "d:\IVBAP\sih_border_survelliance"

# Activate venv
.\venv\Scripts\Activate.ps1

# Check if packages are installed
pip list | Select-String ultralytics

# If missing, reinstall
pip install -r requirements.txt
```

### Frontend won't start
```powershell
cd frontend

# Clear cache and reinstall
Remove-Item -Recurse -Force node_modules
npm install
npm run dev
```

### YOLO model not loading
- First run will download `yolo11n.pt` (~6 MB) automatically
- Requires internet connection
- Will be cached in `~/.cache/torch/hub/`

### No detections appearing
- Wait 5-10 seconds for YOLO model to load on first run
- Check backend console for "Pipeline running" messages
- Refresh the browser page

---

## 📊 Expected Behavior

### On Startup (Backend):
```
[INFO] bordereye.master: Initializing Surveillance Database...
[INFO] bordereye.cameras: All camera pipelines (CAM-01 to CAM-05) initialized and running.
[INFO] bordereye.cameras: [cam-01] Pipeline running -> cam1.mp4
[INFO] bordereye.cameras: [cam-02] Pipeline running -> cam2.mp4
...
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### On Live Monitoring Page:
- 5 camera video feeds playing
- **Bounding boxes** around detected people/vehicles
- **Tracking IDs** for each detection
- **Confidence scores** (e.g., "person 0.89")
- **License plates** extracted from vehicles (CAM-02)
- **Virtual fence alerts** when breached (CAM-04)

---

## 🎓 Next Steps

1. **Test the Live Monitoring**: Open http://localhost:3000/live-monitoring
2. **Try AI Search**: Ask "show me all people detected today" at http://localhost:3000/ai-search
3. **Explore API**: Check http://localhost:8000/docs for all endpoints
4. **Add Personnel**: Upload faces at the Watchlist Management page
5. **Set Virtual Fences**: Draw boundaries on CAM-04

---

## 📦 System Info

- **Python**: 3.13.7
- **Node.js**: v24.11.1
- **PyTorch**: 2.14.0 (CPU mode)
- **YOLO**: ultralytics 8.4.156
- **LLM Provider**: Groq (Llama 3.3 70B)
- **Database**: SQLite + ChromaDB (vector store)
- **Backend**: FastAPI + Uvicorn
- **Frontend**: Next.js 15

---

## ⚠️ Notes

- System runs entirely on **CPU** (no GPU required)
- All AI inference happens **locally** on your machine
- Natural Language Query requires **Groq API key** (already configured in `.env`)
- Videos loop automatically for continuous monitoring demo

---

**For detailed technical documentation, see:** `SETUP_LOCAL.md`
