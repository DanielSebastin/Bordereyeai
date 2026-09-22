from __future__ import annotations

# BorderEye AI Multi-Camera Analytics Runner
#
# Real-time multi-camera detection, tracking, ANPR, and Virtual Fence engine:
#   - CAM-01: Human detection + ByteTrack (cam1.mp4)
#   - CAM-02: Vehicle detection + RapidOCR ANPR (cam2.mp4) ← UPGRADED OCR WORKER
#   - CAM-03: Low-light gradual brightness enhancement (cam1.mp4)
#   - CAM-04: Human detection + Virtual Fence intrusion (cam4.mp4)
#   - CAM-05: Crowd & multi-class surveillance (cam5.mp4)

import asyncio
import datetime
import itertools
import json
import logging
import math
import os
import threading
import time
import traceback
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

warnings.filterwarnings("ignore", message=".*half.*deprecated.*")
warnings.filterwarnings("ignore", message=".*torchvision.*")
try:
    logging.getLogger("ultralytics").setLevel(logging.ERROR)
except Exception:
    pass

import cv2
import numpy as np

try:
    import torch
    TORCH_AVAILABLE = True
except Exception:
    torch = None
    TORCH_AVAILABLE = False

try:
    cv2.setLogLevel(cv2.LOG_LEVEL_ERROR)
except Exception:
    pass

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except Exception:
    YOLO = None
    YOLO_AVAILABLE = False

try:
    from rapidocr_onnxruntime import RapidOCR
    RAPID_OCR_AVAILABLE = True
except Exception:
    RapidOCR = None
    RAPID_OCR_AVAILABLE = False

try:
    import easyocr
    EASY_OCR_AVAILABLE = True
except Exception:
    easyocr = None
    EASY_OCR_AVAILABLE = False

from ..hub import hub
from .anpr_util import refine_plate, complies_format, enhance_plate  # FIX 6: enhance_plate now from anpr_util
from .intrusion import FenceEngine
from .anpr_ocr import ANPRWorker  # ← ANPR Worker import

logger = logging.getLogger("bordereye.cameras")

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
WEIGHTS_PATH = BASE_DIR / "backend" / "weights" / "yolo11n.pt"
DEVICE = "cuda:0" if (TORCH_AVAILABLE and torch and torch.cuda.is_available()) else "cpu"
HALF = bool(TORCH_AVAILABLE and torch and torch.cuda.is_available())

# CPU efficiency: cap torch compute threads so 5 concurrent CPU pipelines
# don't thrash all cores (each inference would otherwise grab every core).
# imgsz is dropped for CPU inference (512 was ~430ms/frame -> near-static feeds);
# 384 keeps vehicle/plate detection quality while giving usable frame rates.
if TORCH_AVAILABLE and torch and not torch.cuda.is_available():
    try:
        _qt = max(1, (os.cpu_count() or 4) // 3)
        torch.set_num_threads(_qt)
        logger = logging.getLogger("bordereye.cameras")
        logger.info(f"CPU mode: torch threads capped to {_qt}")
    except Exception as e:
        print(f"[camera_runner] torch thread config skipped: {e}")

CPU_IMGSZ = int(os.getenv("CPU_IMGSZ", "384"))
IMGSZ = CPU_IMGSZ if DEVICE.startswith("cpu") else 512

_SHARED_YOLO: Optional[Any] = None
_SHARED_OCR: Optional[Any] = None

class CrossCameraRegistry:
    def __init__(self):
        self.lock = threading.Lock()
        self.cam1_persons: Dict[int, Dict[str, Any]] = {}
        self.history: List[Dict[str, Any]] = []

    def register_cam1(self, track_id: int, bbox: list, ts: float):
        with self.lock:
            if track_id not in self.cam1_persons:
                entry = {
                    "track_id": track_id,
                    "first_seen": ts,
                    "last_seen": ts,
                    "bbox": bbox,
                    "camera": "CAM-01",
                    "sector": "Sector 1 (North Gate)",
                }
                self.cam1_persons[track_id] = entry
                self.history.append(entry)
                if len(self.history) > 100:
                    self.history.pop(0)
            else:
                self.cam1_persons[track_id]["last_seen"] = ts
                self.cam1_persons[track_id]["bbox"] = bbox

    def match_cam3(self, track_id: int, bbox: list, ts: float) -> Tuple[bool, Dict[str, Any]]:
        """Return (match_found, info_dict).

        FIX 10 — Previously this always fabricated a match by doing a modular
        wrap of registry keys even when the specific track_id was absent. Now
        it performs a strict lookup: match_found is True only when track_id
        exists in cam1_persons.  Callers must check match_found before labelling
        a person as a cross-camera re-identification.
        """
        with self.lock:
            cam1_entry = self.cam1_persons.get(track_id)  # strict lookup
            if cam1_entry is None:
                # No real match — do NOT fabricate one.
                return False, {}

            first_seen_ts = cam1_entry["first_seen"]
            t_str = time.strftime("%H:%M:%S", time.localtime(first_seen_ts))
            return True, {
                "origin_camera": "CAM-01",
                "origin_sector": "Sector 1 (North Gate)",
                "status": "CROSS_CAMERA_MATCH",
                "alert": "Appeared in CAM-01",
                "message": f"Person #{track_id} appeared in CAM-01 previously",
                "first_seen_cam1": first_seen_ts,
                "first_seen_time": t_str,
            }

CROSS_CAMERA_REGISTRY = CrossCameraRegistry()

class CriminalTrespassRegistry:
    """Tracks trespassers in restricted rooms (CAM-04) and correlates them on apprehension cameras (CAM-05)."""
    def __init__(self):
        self.lock = threading.Lock()
        self.trespassers: Dict[int, Dict[str, Any]] = {}
        self.history: List[Dict[str, Any]] = []

    def register_trespasser(self, track_id: int, bbox: list, ts: float, camera: str = "CAM-04", zone: str = "Restricted Control Room"):
        with self.lock:
            if track_id not in self.trespassers:
                entry = {
                    "track_id": track_id,
                    "first_seen": ts,
                    "last_seen": ts,
                    "bbox": bbox,
                    "origin_camera": camera,
                    "zone": zone,
                    "status": "ACTIVE_TRESPASSER",
                    "threat_level": "CRITICAL",
                    "criminal_id": f"CRIM-90{track_id % 10}",
                }
                self.trespassers[track_id] = entry
                self.history.append(entry)
                if len(self.history) > 100:
                    self.history.pop(0)
            else:
                self.trespassers[track_id]["last_seen"] = ts
                self.trespassers[track_id]["bbox"] = bbox

    def match_criminal(self, track_id: int, bbox: list, ts: float) -> Tuple[bool, Dict[str, Any]]:
        """Return (match_found, info_dict).

        FIX 9 — Previously always returned a populated dict, fabricating a
        criminal match via modular key lookup even when track_id was not a
        registered trespasser. Now performs a strict lookup: match_found is
        True only when track_id exists in the trespassers registry. Callers
        (CAM-05 pipeline) must check match_found before flagging a person.
        """
        with self.lock:
            t_entry = self.trespassers.get(track_id)  # strict lookup
            if t_entry is None:
                # No real match — do NOT fabricate one.
                return False, {}

            first_seen_ts = t_entry["first_seen"]
            t_str = time.strftime("%H:%M:%S", time.localtime(first_seen_ts))
            crim_id = t_entry.get("criminal_id", f"CRIM-90{track_id % 10}")
            return True, {
                "origin_camera": "CAM-04",
                "origin_zone": "Restricted Room (CAM-04)",
                "status": "CRIMINAL_WARNING",
                "is_criminal": True,
                "criminal_id": crim_id,
                "alert": "Known Criminal / Room Trespasser Identified",
                "message": f"Subject #{crim_id} (Trespassed CAM-04 Restricted Room) spotted in CAM-05!",
                "first_seen_cam4": first_seen_ts,
                "first_seen_time": t_str,
                "threat_level": "CRITICAL",
            }

CRIMINAL_TRESPASS_REGISTRY = CriminalTrespassRegistry()

LATEST_CAMERA_STATES: Dict[str, Dict[str, Any]] = {}
_CAMERA_STATE_LOCK = threading.Lock()

def record_camera_state(camera_id: str, state: dict) -> None:
    with _CAMERA_STATE_LOCK:
        LATEST_CAMERA_STATES[camera_id] = state

def get_latest_camera_state(camera_id: str) -> Optional[dict]:
    with _CAMERA_STATE_LOCK:
        return LATEST_CAMERA_STATES.get(camera_id)

def get_all_camera_states() -> Dict[str, Any]:
    with _CAMERA_STATE_LOCK:
        return dict(LATEST_CAMERA_STATES)

def get_shared_yolo() -> Optional[Any]:
    global _SHARED_YOLO
    if _SHARED_YOLO is None and YOLO_AVAILABLE and YOLO is not None:
        try:
            w = resolve_weights()
            _SHARED_YOLO = YOLO(str(w))
            logger.info(f"Loaded Shared YOLO model from {w} (device={DEVICE})")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
    return _SHARED_YOLO

def get_shared_ocr() -> Optional[Any]:
    global _SHARED_OCR
    if _SHARED_OCR is None:
        if RAPID_OCR_AVAILABLE:
            try:
                _SHARED_OCR = RapidOCR()
                logger.info("RapidOCR initialized")
            except Exception as e:
                logger.warning(f"RapidOCR initialization warning: {e}")
        elif EASY_OCR_AVAILABLE:
            try:
                _SHARED_OCR = easyocr.Reader(['en'], gpu=False)
                logger.info("EasyOCR initialized (fallback mode)")
            except Exception as e:
                logger.warning(f"EasyOCR initialization warning: {e}")
    return _SHARED_OCR

def resolve_weights() -> Path:
    candidates = [
        WEIGHTS_PATH,
        BASE_DIR / "yolo11n.pt",
        Path("yolo11n.pt"),
        Path.home() / ".cache" / "ultralytics" / "yolo11n.pt",
]
    for p in candidates:
        if p.exists():
            return p
    return Path("yolo11n.pt")

def resolve_tracker_config() -> str:
    # Use BoTSORT instead of ByteTrack to fix 'Conv' object has no attribute 'bn' error
    return "botsort.yaml"

def resolve_video_path(video_name: str) -> Optional[Path]:
    name_clean = Path(video_name).name
    alt_name = (
        name_clean.replace("cam0", "cam")
        if "cam0" in name_clean
        else name_clean.replace("cam", "cam0")
    )
    search_dirs = [
        BASE_DIR / "frontend" / "public",
        BASE_DIR / "public",
        BASE_DIR / "data",
        BASE_DIR,
        Path("frontend/public"),
        Path("public"),
        Path("data"),
        Path("."),
    ]
    for d in search_dirs:
        p1 = d / name_clean
        if p1.exists():
            return p1.resolve()
        p2 = d / alt_name
        if p2.exists():
            return p2.resolve()
    return None

COCO_LABELS = {
    0: "person",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}
VEHICLE_CLS = ("car", "truck", "bus", "motorcycle")

@dataclass
class CameraPipeline:
    camera_id: str
    video: str
    classes: list[int]
    label_map: dict[int, str]
    conf: float = 0.25
    imgsz: int = 512
    proc_every: int = 1
    frame_cap: int = 30
    anpr: bool = False
    anpr_interval: float = 2.5
    fence: bool = False
    fence_threshold: float = 0.08
    low_light_enhance: bool = False
    enhance_duration: float = 3.0
    efps: float = 0.0

    fence_engine: Optional[FenceEngine] = field(default=None, init=False)
    loop_offset: int = field(default=0, init=False)
    max_id: int = field(default=0, init=False)
    stop: bool = field(default=False, init=False)
    last_frame_at: float = field(default=0.0, init=False)
    plate_results: dict = field(default_factory=dict, init=False)
    ocr_queue: list = field(default_factory=list, init=False)
    ocr_target_at: float = field(default=0.0, init=False)
    epoch: int = field(default=0, init=False)
    reset_requested: bool = field(default=False, init=False)
    t0: float = field(default=0.0, init=False)
    _sync_anchor_set: bool = field(default=False, init=False)
    enhance_start_time: float = field(default=0.0, init=False)
    current_brightness: float = field(default=1.0, init=False)

    def init_pipeline(self) -> None:
        if self.fence:
            self.fence_engine = FenceEngine(threshold=self.fence_threshold)
            self._load_fence()
            if not self.fence_engine.polygon:
                # Default restricted room boundary for cam4
                self.fence_engine.set_polygon([(0.15, 0.20), (0.85, 0.20), (0.85, 0.90), (0.15, 0.90)])

    def _fence_file(self) -> Path:
        return Path("data") / f"{self.camera_id}_fence.json"

    def _save_fence(self) -> None:
        try:
            f = self._fence_file()
            f.parent.mkdir(parents=True, exist_ok=True)
            if self.fence_engine:
                f.write_text(
                    json.dumps({"camera": self.camera_id, "polygon": self.fence_engine.polygon}, indent=2),
                    encoding="utf-8",
                )
        except Exception as e:
            logger.warning(f"[{self.camera_id}] Save fence failed: {e}")

    def _load_fence(self) -> None:
        try:
            f = self._fence_file()
            if f.exists() and self.fence_engine:
                data = json.loads(f.read_text(encoding="utf-8"))
                poly = data.get("polygon")
                if poly:
                    self.fence_engine.set_polygon(poly)
                    logger.info(f"[{self.camera_id}] Loaded persistent virtual fence: {len(self.fence_engine.polygon)} vertices")
        except Exception as e:
            logger.warning(f"[{self.camera_id}] Load fence failed: {e}")

def _normalize(bb_xyxyn, frame_w: int, frame_h: int, class_id: int, label: str, track_id: int, conf: float) -> dict:
    x1, y1, x2, y2 = bb_xyxyn
    return {
        "id": int(track_id),
        "cls": COCO_LABELS.get(int(class_id), "object"),
        "label": label,
        "confidence": round(float(conf), 2),
        "bbox": [round(float(x1), 4), round(float(y1), 4), round(float(x2 - x1), 4), round(float(y2 - y1), 4)],
    }

# FIX 6 — _enhance_plate removed from this file; it is now the shared
# enhance_plate() imported from anpr_util above.
#
# The local _enhance_plate alias below keeps any remaining call-sites in
# this file working without further edits.
_enhance_plate = enhance_plate

# ── Plate deduplication cache ─────────────────────────────────────────────────
# FIX 8 — _PLATE_CACHE_LOCK serialises all read/write/delete access to
# _PLATE_CACHE across multiple OCR worker threads.  Without this lock a
# dict resize during concurrent iteration raises RuntimeError.
_PLATE_CACHE: Dict[str, float] = {}
_PLATE_CACHE_LOCK = threading.Lock()   # FIX 8
_PLATE_CACHE_TTL = 15.0  # seconds to consider a plate as "already seen"
_PLATE_CACHE_MAX_AGE = 60.0

def _clean_plate(text: str) -> str:
    return "".join(c for c in text.upper() if c.isalnum())

def _ocr_plate_crop(ocr, crop_bgr, origin=(0, 0), frame_w=1920, frame_h=1080) -> Optional[dict]:
    ch, cw = crop_bgr.shape[:2]
    if ch < 15 or cw < 20:
        return None
    
    candidates = []
    is_easy_ocr = hasattr(ocr, 'readtext')
    
    # Test 1: Full vehicle crop
    try:
        if is_easy_ocr:
            results = ocr.readtext(crop_bgr)
            for item in results:
                bx, text, score = item
                clean = _clean_plate(text)
                if 4 <= len(clean) <= 12 and score > 0.5:
                    candidates.append((score, clean, bx))
        else:
            res1, _ = ocr(crop_bgr)
            if res1:
                for item in res1:
                    bx, text, score = item
                    clean = _clean_plate(text)
                    if 4 <= len(clean) <= 12 and score > 0.8:
                        candidates.append((score, clean, bx))
    except Exception:
        pass

    # Test 2: Enhanced lower band
    if not candidates:
        try:
            band = crop_bgr[int(ch * 0.35):, :]
            if band.shape[0] > 14 and band.shape[1] > 20:
                enhanced = _enhance_plate(band)
                if is_easy_ocr:
                    results = ocr.readtext(enhanced)
                    for item in results:
                        bx, text, score = item
                        clean = _clean_plate(text)
                        if 4 <= len(clean) <= 12 and score > 0.5:
                            candidates.append((score, clean, bx))
                else:
                    res2, _ = ocr(enhanced)
                    if res2:
                        for item in res2:
                            bx, text, score = item
                            clean = _clean_plate(text)
                            if 4 <= len(clean) <= 12 and score > 0.8:
                                candidates.append((score, clean, bx))
        except Exception:
            pass

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    score, label, bx = candidates[0]
    
    ox, oy = origin
    xs = [int(p[0]) + ox for p in bx]
    ys = [int(p[1]) + oy for p in bx]
    x_min, x_max = max(0, min(xs)), min(frame_w, max(xs))
    y_min, y_max = max(0, min(ys)), min(frame_h, max(ys))
    
    bbox_norm = [
        round(x_min / frame_w, 4),
        round(y_min / frame_h, 4),
        round(max(0.025, (x_max - x_min) / frame_w), 4),
        round(max(0.02, (y_max - y_min) / frame_h), 4),
    ]

    return {
        "cls": "plate",
        "label": label,
        "confidence": round(float(score), 2),
        "bbox": bbox_norm,
        "plate": label,
    }

def _persist_detection(camera_id: str, event_type: str, severity: str, description: str, metadata: Optional[dict] = None):
    """Best-effort persistence of events/vehicles so dashboard lists populate."""
    try:
        from ..database.db_session import SessionLocal
        from ..database.models import SurveillanceEvent, VehicleRecord
        db = SessionLocal()
        try:
            ev = SurveillanceEvent(
                camera_id=camera_id,
                event_type=event_type,
                severity=severity,
                timestamp=datetime.datetime.utcnow(),
                description=description,
                metadata_json=metadata or {},
            )
            db.add(ev)
            if event_type == "anpr" and metadata and metadata.get("plate"):
                db.add(VehicleRecord(
                    camera_id=camera_id,
                    license_plate=metadata.get("plate"),
                    vehicle_type=metadata.get("vehicle_type") or "car",
                    timestamp=datetime.datetime.utcnow(),
                ))
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
    except Exception:
        pass


def ocr_worker(p: CameraPipeline):
    """Background OCR worker for pipelines that do NOT use ANPRWorker.

    FIX 4  — ``now`` is refreshed on every iteration so TTL comparisons
              are always accurate (previously computed once at thread start).
    FIX 8  — _PLATE_CACHE reads/writes guarded by _PLATE_CACHE_LOCK.
    """
    ocr = get_shared_ocr()
    logger.info(f"[{p.camera_id}] OCR background worker started")

    # Initial cache sweep — uses a fresh timestamp.
    with _PLATE_CACHE_LOCK:   # FIX 8
        _sweep_plate_cache()

    while not p.stop:
        if not p.ocr_queue:
            time.sleep(0.06)
            continue
        try:
            crop_bgr, origin, ts, veh_id, epoch = p.ocr_queue.pop(0)
            if epoch != p.epoch or ocr is None:
                continue
            plate = _ocr_plate_crop(ocr, crop_bgr, origin=origin)
            if plate:
                plate_label = plate["label"]
                cache_key = f"{p.camera_id}:{plate_label}"
                now = time.time()   # FIX 4: refresh now inside loop
                # FIX 8: guard cache read under lock
                with _PLATE_CACHE_LOCK:
                    already_seen = (
                        cache_key in _PLATE_CACHE
                        and (now - _PLATE_CACHE[cache_key]) < _PLATE_CACHE_TTL
                    )
                if already_seen:
                    continue
                plate["at"] = ts
                plate["ox"], plate["oy"] = origin
                plate["veh_id"] = veh_id
                plate["epoch"] = epoch
                p.plate_results[veh_id] = plate
                with _PLATE_CACHE_LOCK:   # FIX 8: guard cache write under lock
                    _PLATE_CACHE[cache_key] = ts
                logger.info(f"[{p.camera_id}][ANPR] Detected Plate: {plate_label} for Vehicle #{veh_id}")
                _persist_detection(
                    p.camera_id,
                    "anpr",
                    "warn",
                    f"ANPR detected plate {plate_label} on vehicle #{veh_id}",
                    {"plate": plate_label, "vehicle_type": "car"},
                )
        except Exception as e:
            logger.warning(f"[{p.camera_id}] OCR worker exception: {e}")


def _sweep_plate_cache() -> None:
    """Evict entries older than _PLATE_CACHE_MAX_AGE. Caller must hold _PLATE_CACHE_LOCK."""
    now = time.time()
    stale = [k for k, ts in _PLATE_CACHE.items() if now - ts > _PLATE_CACHE_MAX_AGE]
    for k in stale:
        del _PLATE_CACHE[k]

def _queue_plate_crop(p: CameraPipeline, frame, x1: int, y1: int, x2: int, y2: int, ts: float, veh: Optional[dict] = None):
    h, w = frame.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    if x2 <= x1 or y2 <= y1:
        return
    crop = frame[y1:y2, x1:x2].copy()
    veh_id = veh["id"] if veh else 0
    p.ocr_queue.append((crop, (x1, y1), ts, veh_id, p.epoch))
    if len(p.ocr_queue) > 6:
        p.ocr_queue.pop(0)

def _merge_plates(p: CameraPipeline, objects: list[dict], frame_w: int, frame_h: int):
    now_t = time.time()
    seen_plates = set()
    # Expire old plate entries
    expired_ids = []
    for v_id, pe in p.plate_results.items():
        if (now_t - pe.get("at", 0)) > 10.0 or pe.get("epoch") != p.epoch:
            expired_ids.append(v_id)
    for v_id in expired_ids:
        del p.plate_results[v_id]
    for veh in objects:
        if veh["cls"] not in VEHICLE_CLS:
            continue
        v_id = veh["id"]
        plate_entry = p.plate_results.get(v_id)
        if not plate_entry:
            # Check by bounding box overlap
            vx, vy, vw, vh = veh["bbox"]
            for pid, pe in p.plate_results.items():
                if pe.get("label") in seen_plates:
                    continue
                px, py, pw, ph = pe.get("bbox", [0, 0, 0, 0])
                if vx <= (px + pw / 2) <= (vx + vw) and vy <= (py + ph / 2) <= (vy + vh):
                    plate_entry = pe
                    break
        if not plate_entry:
            continue
        plate_label = plate_entry["label"]
        # Skip if already seen in this frame
        if plate_label in seen_plates:
            continue
        veh["plate"] = plate_label
        veh["label"] = f"{veh['cls'].capitalize()} [{plate_label}]"
        seen_plates.add(plate_label)
    # Emit separate plate objects (deduplicated)
    for v_id, plate_entry in list(p.plate_results.items()):
        plate_label = plate_entry["label"]
        if plate_label in seen_plates:
            continue
        objects.append({
            "id": 9000 + (v_id % 1000),
            "cls": "plate",
            "label": f"Plate: {plate_entry['label']}",
            "confidence": plate_entry.get("confidence", 0.94),
            "bbox": plate_entry.get("bbox", [0.4, 0.7, 0.08, 0.03]),
            "plate": plate_entry["label"],
        })
        seen_plates.add(plate_label)

def _counts(camera_id: str, objects: list[dict]) -> dict:
    counts: dict = {"total": len(objects)}
    counts["humans"] = sum(1 for o in objects if o["cls"] == "person")
    counts["vehicles"] = sum(1 for o in objects if o["cls"] in VEHICLE_CLS)
    counts["plates"] = sum(1 for o in objects if "plate" in o or o["cls"] == "plate")
    return counts

# ── PIPELINE DEFINITIONS ──────────────────────────────────────────────────────
PIPELINES = [
    CameraPipeline(
        camera_id="cam-01",
        video="cam1.mp4",
        classes=[0],
        label_map={0: "person"},
        conf=0.25,
        imgsz=IMGSZ,
        proc_every=1,
        frame_cap=30,
    ),
    CameraPipeline(
        camera_id="cam-02",
        video="cam2.mp4",
        classes=[0, 2, 3, 5, 7],
        label_map={0: "person", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck"},
        conf=0.25,
        imgsz=IMGSZ,
        proc_every=1,
        frame_cap=30,
        anpr=True,
        anpr_interval=2.0,
    ),
    CameraPipeline(
        camera_id="cam-03",
        video="cam1.mp4",
        classes=[0, 2, 3, 5, 7],
        label_map={0: "person", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck"},
        conf=0.25,
        imgsz=IMGSZ,
        proc_every=1,
        frame_cap=30,
        low_light_enhance=True,
        enhance_duration=3.0,
    ),
    CameraPipeline(
        camera_id="cam-04",
        video="cam4.mp4",
        classes=[0],
        label_map={0: "person"},
        conf=0.22,
        imgsz=IMGSZ,
        proc_every=1,
        frame_cap=15,  # Slowed down from 30 to reduce fast playback
        fence=True,
        fence_threshold=0.08,
    ),
    CameraPipeline(
        camera_id="cam-05",
        video="cam5.mp4",
        classes=[0, 2, 3, 5, 7],
        label_map={0: "person", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck"},
        conf=0.25,
        imgsz=IMGSZ,
        proc_every=1,
        frame_cap=30,
    ),
]

def run_pipeline(p: CameraPipeline, loop: asyncio.AbstractEventLoop) -> None:
    video_path = resolve_video_path(p.video)
    if not video_path:
        logger.error(f"[{p.camera_id}] Video file not found: {p.video}")
        return

    tracker_config = resolve_tracker_config()
    model = get_shared_yolo()
    logger.info(f"[{p.camera_id}] Pipeline running -> {video_path.name} (tracker={tracker_config})")

    # ── Initialize ANPR Worker (CAM-02 only) ──
    anpr_worker = None
    if p.camera_id == "cam-02" and p.anpr:
        anpr_worker = ANPRWorker(camera_id=p.camera_id, ocr_mode="clone")  # Use EasyOCR clone mode like bordereye-ai
        logger.info(f"[{p.camera_id}] ANPR Worker initialized (non-blocking OCR)")

    while not p.stop:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.error(f"[{p.camera_id}] Failed to open video: {video_path}")
            time.sleep(2.0)
            continue

        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1000
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
        frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720
        loop_start_id = p.loop_offset
        frame_index = -1
        seq = 0

        if p.fence and p.fence_engine:
            p.fence_engine.clear_tracks()

        if not p._sync_anchor_set:
            p.t0 = time.time()
        else:
            p._sync_anchor_set = False

        p.epoch += 1
        p.plate_results.clear()
        p.ocr_queue.clear()
        p.ocr_target_at = 0.0
        p.efps = 0.0
        if p.low_light_enhance:
            p.enhance_start_time = time.time()
            p.current_brightness = 0.2

        first_after_open = True
        session_first_sent = False

        try:
            while not p.stop:
                if p.reset_requested:
                    p.reset_requested = False
                    p.loop_offset = 0
                    p.max_id = 0
                    break

                ret, frame = cap.read()
                if not ret:
                    break

                frame_index += 1
                if frame_index % p.proc_every != 0:
                    continue

                # Frame sync: smooth playback without skipping frames
                # If we process faster than the video FPS, throttle. If we process slower, let it run in smooth slow-motion.
                target_time = p.t0 + (frame_index / fps)
                now = time.time()
                if now < target_time:
                    time.sleep(target_time - now)

                if p.low_light_enhance:
                    elapsed = time.time() - p.enhance_start_time
                    if elapsed < p.enhance_duration:
                        progress = elapsed / p.enhance_duration
                        eased = 1.0 - pow(1.0 - progress, 3)
                        p.current_brightness = 0.2 + (0.8 * eased)
                    else:
                        p.current_brightness = 1.0
                    if p.current_brightness < 1.0:
                        frame = cv2.convertScaleAbs(frame, alpha=p.current_brightness, beta=0)

                t_start = time.time()
                objects: list[dict] = []

                if model is not None:
                    try:
                        # Use track() to maintain persistent object IDs across frames
                        # Essential for cross-camera re-id, ANPR tracking, and virtual fence
                        results = model.track(
                            source=frame,
                            persist=True,
                            tracker=p.tracker_config,
                            verbose=False,
                            conf=p.conf,
                            iou=0.6,
                            classes=p.classes,
                            imgsz=p.imgsz,
                            device=DEVICE,
                            half=HALF,
                            max_det=50,
                        )[0]
                        first_after_open = False
                        boxes = results.boxes
                        if boxes is not None and boxes.xyxyn is not None and len(boxes) > 0:
                            # Extract true tracking IDs assigned by ByteTrack/BoTSORT
                            for idx, (xyxy_n, c_id, score) in enumerate(zip(
                                boxes.xyxyn.tolist(),
                                boxes.cls.tolist(),
                                boxes.conf.tolist(),
                            )):
                                if boxes.id is not None and len(boxes.id) > idx:
                                    tid = int(boxes.id[idx].item())
                                else:
                                    tid = loop_start_id + seq * 50 + idx + 1
                                p.max_id = max(p.max_id, tid)
                                label = p.label_map.get(int(c_id), COCO_LABELS.get(int(c_id), "object"))
                                objects.append(
                                    _normalize(
                                        xyxy_n,
                                        frame_w,
                                        frame_h,
                                        c_id,
                                        label,
                                        tid,
                                        score,
                                    )
                                )
                    except Exception as e:
                        logger.warning(f"[{p.camera_id}] Detection error: {e}")

                dt = time.time() - t_start
                inst = (1.0 / dt) if dt > 0 else 0.0
                p.efps = (p.efps * 0.85 + inst * 0.15) if p.efps else inst

                # ── ANPR plate recognition on vehicles (CAM-02) ── UPGRADED TO WORKER THREAD ──
                if anpr_worker and p.camera_id == "cam-02":
                    now2 = time.time()
                    # Rate limiting: OCR every 2.5s per vehicle
                    if (now2 - p.ocr_target_at) >= p.anpr_interval:
                        vehs = [o for o in objects if o["cls"] in VEHICLE_CLS and o["bbox"][2] > 0.04]
                        
                        for veh in vehs[:4]:  # Process up to 4 vehicles per interval
                            track_id = veh.get("id", 0)
                            if track_id <= 0:
                                continue
                            
                            # Extract vehicle crop
                            x1, y1, w, h = veh["bbox"]
                            ox, oy = int(x1 * frame_w), int(y1 * frame_h)
                            ox2, oy2 = int((x1 + w) * frame_w), int((y1 + h) * frame_h)
                            
                            # Crop vehicle region
                            veh_crop = frame[oy:oy2, ox:ox2]
                            if veh_crop.size > 0:
                                # Queue for background OCR (non-blocking)
                                anpr_worker.queue_vehicle_crop(track_id, veh_crop, frame_w, frame_h)
                        
                        p.ocr_target_at = now2
                    
                    # Attach cached plates to vehicles (from worker results)
                    current_vehicle_ids = []
                    for veh in objects:
                        if veh["cls"] in VEHICLE_CLS:
                            track_id = veh.get("id", 0)
                            if track_id > 0:
                                current_vehicle_ids.append(track_id)
                                plate = anpr_worker.get_plate(track_id)
                                if plate:
                                    veh["plate"] = plate
                                    veh["label"] = f"{veh['cls'].title()} #{track_id} [{plate}]"
                    
                    # Cleanup expired plate results
                    anpr_worker.cleanup_old_results(current_vehicle_ids)

                # Cross-camera tracking: CAM-01 sightings & CAM-03 transitions
                cross_events = []
                if p.camera_id == "cam-01":
                    for o in objects:
                        if o.get("cls") == "person":
                            CROSS_CAMERA_REGISTRY.register_cam1(o["id"], o["bbox"], time.time())
                elif p.camera_id == "cam-03":
                    for o in objects:
                        if o.get("cls") == "person":
                            # FIX 10 — unpack (match_found, info); only label when real match.
                            match_found, match_info = CROSS_CAMERA_REGISTRY.match_cam3(
                                o["id"], o["bbox"], time.time()
                            )
                            if match_found:
                                o["cross_cam"] = "CAM-01"
                                o["cross_camera_alert"] = "Appeared in CAM-01"
                                o["previous_location"] = "CAM-01 (North Gate)"
                                o["label"] = f"Person #{o['id']} [Appeared in CAM-01]"
                                o["status"] = "CROSS_CAMERA_MATCH"
                                o["cross_camera"] = match_info
                                cross_events.append({
                                    "person_id": o["id"],
                                    "title": "Cross-Camera Re-ID",
                                    "message": f"Person #{o['id']} crossed CAM-01 and appeared in CAM-03",
                                    "origin": "CAM-01",
                                    "current": "CAM-03",
                                    "timestamp": int(time.time() * 1000),
                                })

                # Virtual fence & Trespasser intrusion evaluation (CAM-04)
                if p.fence and p.fence_engine is not None:
                    entries = [
                        (
                            [
                                o["bbox"][0],
                                o["bbox"][1],
                                o["bbox"][0] + o["bbox"][2],
                                o["bbox"][1] + o["bbox"][3],
                            ],
                            o["id"],
                        )
                        for o in objects
                        if o["cls"] == "person"
                    ]
                    persons, new_events = p.fence_engine.evaluate(entries)
                    for o in objects:
                        if o["cls"] == "person":
                            p_state = next((px["state"] for px in persons if px["track_id"] == o["id"]), "normal")
                            if p_state == "intrusion":
                                o["state"] = "intrusion"
                                o["is_trespasser"] = True
                                o["threat_level"] = "CRITICAL"
                                o["label"] = f"🚨 TRESPASSER #{o['id']} [Room Intrusion]"
                                CRIMINAL_TRESPASS_REGISTRY.register_trespasser(o["id"], o["bbox"], time.time(), "CAM-04", "Restricted Room")
                    frame_state_persons = persons
                    frame_state_events = new_events
                    frame_state_fence = p.fence_engine.polygon
                    frame_state_counts = {
                        "persons": len(persons),
                        "approaching": sum(1 for x in persons if x["state"] == "approaching"),
                        "intrusion": sum(1 for x in persons if x["state"] == "intrusion"),
                    }
                else:
                    frame_state_persons = None
                    frame_state_events = None
                    frame_state_fence = None
                    frame_state_counts = None

                # Criminal list identification & Apprehension Warning (CAM-05)
                # FIX 9 — Only mark a person as criminal when match_criminal()
                # returns an ACTUAL registry hit (match_found=True).
                # Previously every person in CAM-05 was unconditionally flagged.
                criminal_events = []
                if p.camera_id == "cam-05":
                    for o in objects:
                        if o.get("cls") == "person":
                            match_found, crim_info = CRIMINAL_TRESPASS_REGISTRY.match_criminal(
                                o["id"], o["bbox"], time.time()
                            )
                            if match_found:   # FIX 9: real match required
                                o["is_criminal"] = True
                                o["status"] = "CRIMINAL_WARNING"
                                o["label"] = f"🚨 WANTED CRIMINAL #{o['id']} [CAM-04 Trespasser]"
                                o["warning"] = "Criminal Watchlist Match · Restricted Room Trespasser"
                                o["threat_level"] = "CRITICAL"
                                o["criminal_info"] = crim_info
                                criminal_events.append({
                                    "person_id": o["id"],
                                    "title": "CRIMINAL WATCHLIST WARNING",
                                    "message": (
                                        f"🚨 Criminal #{crim_info['criminal_id']} "
                                        f"(Trespassed CAM-04 Restricted Room) identified in CAM-05!"
                                    ),
                                    "origin": "CAM-04",
                                    "current": "CAM-05",
                                    "severity": "critical",
                                    "timestamp": int(time.time() * 1000),
                                })

                frame_state = {
                    "type": "frame",
                    "camera": p.camera_id,
                    "seq": seq,
                    "ts": int(time.time() * 1000),
                    "vts": round(frame_index / fps, 3),
                    "vfps": round(fps, 2),
                    "efps": round(p.efps, 2),
                    "tracking": True,
                    "first": not session_first_sent,
                    "objects": objects,
                    "counts": _counts(p.camera_id, objects),
                }

                if cross_events:
                    frame_state["cross_camera_events"] = cross_events
                    frame_state["cross_camera_alert"] = cross_events[0]

                if criminal_events:
                    frame_state["criminal_events"] = criminal_events
                    frame_state["criminal_warning_alert"] = criminal_events[0]

                if frame_state_persons is not None:
                    frame_state["persons"] = frame_state_persons
                    frame_state["events"] = frame_state_events
                    frame_state["fence"] = frame_state_fence
                    frame_state["counts"] = frame_state_counts

                if not session_first_sent:
                    p.t0 = time.time() - frame_index / fps
                    session_first_sent = True

                seq += 1
                record_camera_state(p.camera_id, frame_state)
                if loop and loop.is_running():
                    asyncio.run_coroutine_threadsafe(hub.broadcast_camera(p.camera_id, frame_state), loop)

        finally:
            cap.release()

        # Reset offsets to prevent IDs from exploding to infinity over hours of looping
        p.loop_offset = 0

def get_pipeline(camera_id: str) -> Optional[CameraPipeline]:
    for p in PIPELINES:
        if p.camera_id == camera_id:
            return p
    return None

def start_all_pipelines(loop: asyncio.AbstractEventLoop) -> None:
    """Initialise and start all camera pipeline threads.

    FIX 15 — The legacy ocr_worker thread has been removed for ANPR cameras.
    ANPRWorker (spawned inside run_pipeline for cam-02) is the sole OCR
    mechanism. Starting two competing OCR workers for the same camera was
    wasting CPU and silently discarding one set of results.
    """
    get_shared_yolo()
    for p in PIPELINES:
        p.stop = False
        p.init_pipeline()
        # FIX 15: do NOT start a separate ocr_worker thread for ANPR cameras.
        # ANPRWorker inside run_pipeline handles OCR on its own thread.
        threading.Thread(target=run_pipeline, args=(p, loop), daemon=True, name=f"{p.camera_id}-runner").start()
    logger.info("All camera pipelines (CAM-01 to CAM-05) initialised and running.")

def stop_all_pipelines() -> None:
    for p in PIPELINES:
        p.stop = True
    logger.info("All camera pipelines stopped.")
