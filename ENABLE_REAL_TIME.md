# 🚀 Enable Real-Time AI Inference in Their System

## ✅ Good News!

Their system already has:
- ✅ Your AI inference engine code (copied from YOUR BorderEye AI)
- ✅ 5 video files (cam1.mp4 to cam5.mp4)
- ✅ Complete pipeline architecture
- ✅ YOLO, ByteTrack, ANPR, Virtual Fence

**Problem:** Video paths aren't being found, so inference never starts.

---

## 🔧 Quick Fix Steps

### Step 1: Verify Video Files Are Accessible

```powershell
# Check videos exist
Get-ChildItem d:\IVBAP\sih_border_survelliance\*.mp4
```

**Expected:**
- cam1.mp4 (10.6 MB) - Humans
- cam2.mp4 (8.5 MB) - Vehicles  
- cam3.mp4 (10.6 MB) - Low-light
- cam4.mp4 (3.0 MB) - Virtual fence
- cam5.mp4 (2.7 MB) - Crowd

### Step 2: Download YOLO Weights

Their system needs `yolo11n.pt`:

```powershell
# Create weights directory
New-Item -ItemType Directory -Path "d:\IVBAP\sih_border_survelliance\backend\weights" -Force

# Copy from YOUR system (if you have it)
Copy-Item "d:\IVBAP\bordereye-ai\backend\weights\yolo11n.pt" "d:\IVBAP\sih_border_survelliance\backend\weights\yolo11n.pt"
```

**OR download fresh:**
```python
# Inside container
from ultralytics import YOLO
model = YOLO('yolo11n.pt')  # Auto-downloads
```

### Step 3: Fix Video Path Resolution

Edit their `camera_runner.py` to use absolute paths:

**Current code (line ~280):**
```python
def resolve_video_path(video_name: str) -> Optional[Path]:
    search_dirs = [
        BASE_DIR / "frontend" / "public",
        BASE_DIR / "public",
        BASE_DIR / "data",
        BASE_DIR,
        # ...
    ]
```

**Add Docker-specific path:**

Create file: `d:\IVBAP\sih_border_survelliance\backend\app\vision\video_paths.py`

```python
# Video path overrides for Docker
VIDEO_PATHS = {
    "cam1.mp4": "/app/cam1.mp4",
    "cam2.mp4": "/app/cam2.mp4",
    "cam3.mp4": "/app/cam3.mp4",
    "cam4.mp4": "/app/cam4.mp4",
    "cam5.mp4": "/app/cam5.mp4",
}
```

---

## 🐳 Better Approach: Update docker-compose.yml

Add video files as volumes so the backend can access them:

```yaml
services:
  backend:
    image: ghcr.io/praveen21-tech/sih_border_survelliance/backend:latest
    volumes:
      - bordereye-data:/app/data
      # ADD THESE LINES:
      - ./cam1.mp4:/app/cam1.mp4:ro
      - ./cam2.mp4:/app/cam2.mp4:ro
      - ./cam3.mp4:/app/cam3.mp4:ro
      - ./cam4.mp4:/app/cam4.mp4:ro
      - ./cam5.mp4:/app/cam5.mp4:ro
```

---

## 🎯 Complete Fix Script

Run this to enable real-time inference:

```powershell
cd d:\IVBAP\sih_border_survelliance

# 1. Stop current containers
$env:PATH = "C:\Users\acer\AppData\Local\Programs\DockerDesktop\resources\bin;$env:PATH"
docker compose down

# 2. Update docker-compose.yml to mount videos
# (I'll do this for you in next step)

# 3. Rebuild and restart
docker compose up --build -d

# 4. Watch logs for AI inference
docker logs -f bordereye-backend | Select-String "YOLO|Pipeline|Detection"
```

---

## 📝 What Will Happen

Once fixed:

```
[cam-01] Pipeline running -> cam1.mp4 (tracker=bytetrack.yaml)
[cam-01] Loaded Shared YOLO model from yolo11n.pt (device=cpu)
[cam-01] Person #1 detected at (0.23, 0.45)
[cam-01] Broadcasting to 2 WebSocket clients
[cam-02] Vehicle #3 detected: Car [KA01AB1234]
[cam-02][ANPR] Detected Plate: KA01AB1234 for Vehicle #3
[cam-03] Low-light enhancement: brightness=0.45
[cam-04] TRESPASSER #2 [Room Intrusion] detected!
[cam-05] Cross-Camera Re-ID: Person #1 appeared in CAM-01
```

---

## 🔥 Fastest Solution: Just Update docker-compose

Let me update their docker-compose.yml with video mounts:

