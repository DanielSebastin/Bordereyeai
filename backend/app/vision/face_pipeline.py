from __future__ import annotations
# BorderEye AI — CAM06 Live Facial Recognition & Access Control Pipeline
#
# Detects faces, matches against enrolled authorized personnel, categorizes
# all unrecognized faces as INTRUDERS, and streams real-time access alerts.
# Supports runtime camera selection via API.

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

import cv2
import numpy as np

from .face_detector import FaceDetector
from .face_recognizer import FaceRecognizer
from .watchlist_manager import WatchlistManager

logger = logging.getLogger("bordereye.face_pipeline")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ALERT_LOG = BASE_DIR / "data" / "face_alerts.json"

CAMERA_ID = "cam-06"
MATCH_THRESHOLD = 0.46
MIN_DET_SCORE = 0.35
MAX_FACES = 6
PROCESS_EVERY_S = 0.12
KEEP_ALERTS = 50

WL_COLOR = (34, 197, 94)        # BGR Green  — Authorized
INTRUDER_COLOR = (50, 50, 239)   # BGR Red    — Intruder


# ── State ─────────────────────────────────────────────────────────────────────
@dataclass
class FacePipelineState:
    camera_id: str = CAMERA_ID
    kind: str = "webcam"
    stop: bool = False
    seq: int = 0
    t0: float = 0.0
    efps: float = 0.0
    webcam: bool = False
    frames_read: int = 0
    last_process_at: float = 0.0
    objects: list[dict] = field(default_factory=list)
    counts: dict = field(default_factory=dict)
    alerts: list[dict] = field(default_factory=list)
    annotated: Optional[np.ndarray] = field(default=None, repr=False)
    raw_frame: Optional[np.ndarray] = field(default=None, repr=False)
    annotated_dims: tuple[int, int] = (640, 480)
    lock: threading.RLock = field(default_factory=threading.RLock)
    tracker: dict[int, dict] = field(default_factory=dict)
    next_id: int = 1
    # Camera selection
    selected_camera_index: int = 0
    camera_change_requested: bool = False


FACE_PIPELINE = FacePipelineState()
_broadcast = None
_broadcast_lock = threading.Lock()


def set_broadcaster(fn) -> None:
    global _broadcast
    with _broadcast_lock:
        _broadcast = fn


def _emit(payload: dict) -> None:
    with _broadcast_lock:
        fn = _broadcast
    if fn:
        try:
            fn(payload)
        except Exception:
            pass


# ── Face association (IoU tracker) ────────────────────────────────────────────
def _iou_px(a: tuple, b: tuple) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0.0:
        return 0.0
    a_area = (ax2 - ax1) * (ay2 - ay1)
    b_area = (bx2 - bx1) * (by2 - by1)
    return inter / (a_area + b_area - inter)


def _track(faces: list[dict], prev: dict[int, dict], now: float) -> list[tuple[int, list, float]]:
    results: list[tuple[int, list, float]] = []
    taken: set[int] = set()
    for f in faces:
        fb = f["bbox"]
        best_id, best_iou, best_box = None, 0.25, None
        for tid, rec in prev.items():
            if tid in taken:
                continue
            if now - rec["ts"] > 2.5:
                continue
            pb = (rec["cx"] - rec["w"] / 2, rec["cy"] - rec["h"] / 2,
                  rec["cx"] + rec["w"] / 2, rec["cy"] + rec["h"] / 2)
            iou = _iou_px(fb, pb)
            if iou > best_iou:
                best_iou, best_id, best_box = iou, tid, pb
        fid = best_id
        if fid is None:
            fid = FACE_PIPELINE.next_id
            FACE_PIPELINE.next_id += 1
        else:
            taken.add(fid)
        results.append((fid, fb, f["det_score"]))
    return results


# ── Alerts ────────────────────────────────────────────────────────────────────
def _append_alert(status: str, name: str, designation: str, confidence: float) -> dict:
    now = time.time()
    is_auth = (status == "AUTHORIZED")
    alert = {
        "id": f"FA-{int(now * 1000) % 100000}",
        "ts": int(now * 1000),
        "time": datetime.now().strftime("%H:%M:%S"),
        "camera": "CAM-06",
        "cameraName": "CAM-06 Access Control",
        "type": "Authorized Entry" if is_auth else "Intruder Alert",
        "name": name,
        "designation": designation,
        "status": status,
        "confidence": round(confidence, 3),
        "severity": "low" if is_auth else "critical",
        "description": f"Access granted to {name} ({designation})" if is_auth else f"UNAUTHORIZED INTRUDER detected at Sector 1 Checkpoint Access",
    }
    with FACE_PIPELINE.lock:
        FACE_PIPELINE.alerts.insert(0, alert)
        del FACE_PIPELINE.alerts[KEEP_ALERTS:]
    _persist_alerts()
    return alert


def _persist_alerts() -> None:
    try:
        ALERT_LOG.parent.mkdir(parents=True, exist_ok=True)
        ALERT_LOG.write_text(json.dumps(FACE_PIPELINE.alerts, indent=2), encoding="utf-8")
    except Exception:
        pass


def _load_alerts() -> None:
    try:
        if ALERT_LOG.exists():
            FACE_PIPELINE.alerts = json.loads(ALERT_LOG.read_text(encoding="utf-8"))
    except Exception:
        FACE_PIPELINE.alerts = []


# ── Camera selection ──────────────────────────────────────────────────────────
def _open_camera(camera_index: int = 0):
    """Open a specific camera by index with read timeout. Returns (cap, dims, is_webcam, actual_index)."""
    import threading
    
    def try_read(cap_obj, result_list):
        """Helper to read frame in thread with timeout"""
        try:
            ret, frame = cap_obj.read()
            result_list.append((ret, frame))
        except Exception as e:
            result_list.append((False, None))
    
    for backend in (cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY):
        cap = cv2.VideoCapture(camera_index, backend)
        if cap.isOpened():
            # Set buffer size to 1 to reduce lag
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Try reading with 3-second timeout
            result = []
            read_thread = threading.Thread(target=try_read, args=(cap, result), daemon=True)
            read_thread.start()
            read_thread.join(timeout=3.0)
            
            if result and result[0][0] and result[0][1] is not None:
                frame = result[0][1]
                h, w = frame.shape[:2]
                logger.info(f"[cam-06] Camera {camera_index} opened: {w}x{h} via {backend}")
                return cap, (h, w), True, camera_index
            
            # Timeout or failed read
            logger.warning(f"[cam-06] Camera {camera_index} backend {backend} failed/timeout")
            cap.release()
    
    logger.error(f"[cam-06] Camera {camera_index} unavailable on all backends")
    return None, (480, 640), False, None


def get_available_cameras() -> list[dict]:
    """Scan for available hardware cameras and return their info."""
    available = []
    for idx in range(5):
        cap = None
        for backend in (cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY):
            cap = cv2.VideoCapture(idx, backend)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    h, w = frame.shape[:2]
                    available.append({
                        "index": idx,
                        "name": f"Camera {idx}",
                        "resolution": f"{w}x{h}",
                    })
                    cap.release()
                    cap = None
                    break
                cap.release()
                cap = None
        if cap is not None:
            cap.release()
    return available


def set_camera_index(index: int) -> dict:
    """Change the active camera index. Triggers hot-swap on next loop."""
    with FACE_PIPELINE.lock:
        FACE_PIPELINE.selected_camera_index = index
        FACE_PIPELINE.camera_change_requested = True
    logger.info(f"[cam-06] Camera change requested to index {index}")
    return {"success": True, "camera_index": index}


# ── Pipeline loop ─────────────────────────────────────────────────────────────
def run_webcam_pipeline(state: FacePipelineState = FACE_PIPELINE) -> None:
    """Blocking loop; run on its own daemon thread (see main.py startup)."""
    import queue as _queue

    detector = FaceDetector(det_size=320, min_det_score=MIN_DET_SCORE)
    manager = WatchlistManager()
    recognizer = FaceRecognizer(manager, threshold=MATCH_THRESHOLD)

    if manager.watchlist_ready():
        logger.info(f"[cam-06] Watchlist loaded: {manager.embedding_count()} embedding(s) "
                     f"for {[p['name'] for p in manager.get_people()]}")
    else:
        logger.warning("[cam-06] Watchlist is EMPTY — run train_watchlist to enroll faces")

    _load_alerts()
    state.t0 = time.time()

    # ── Thread-safe detection queue ────────────────────────────────────────────
    # Producer: capture loop puts raw frames here.
    # Consumer: detector_thread picks them up and runs InsightFace.
    _frame_q: _queue.Queue = _queue.Queue(maxsize=2)
    _result_q: _queue.Queue = _queue.Queue(maxsize=4)

    def _detector_thread():
        """InsightFace runs here — completely isolated from capture/HTTP."""
        while not state.stop:
            try:
                frame = _frame_q.get(timeout=0.5)
            except _queue.Empty:
                continue
            try:
                faces = detector.recognize(frame, max_num=MAX_FACES)
            except Exception as e:
                logger.error(f"[cam-06] Detection error: {e}")
                faces = []
            try:
                _result_q.put_nowait((frame, faces))
            except _queue.Full:
                try:
                    _result_q.get_nowait()
                except _queue.Empty:
                    pass
                try:
                    _result_q.put_nowait((frame, faces))
                except _queue.Full:
                    pass

    det_thread = threading.Thread(target=_detector_thread, daemon=True, name="cam06-insightface")
    det_thread.start()
    logger.info("[cam-06] InsightFace detector thread started.")

    while not state.stop:
        # Read selected camera index
        with state.lock:
            selected_idx = state.selected_camera_index
            state.camera_change_requested = False

        cap, dims, is_real_webcam, actual_idx = _open_camera(selected_idx)
        if cap is None:
            state.webcam = False
            logger.warning(f"[cam-06] Camera {selected_idx} unavailable — retrying in 10s")
            time.sleep(10.0)
            continue

        state.webcam = is_real_webcam
        state.annotated_dims = dims
        logger.info(f"[cam-06] Access Control active (Camera {actual_idx}, {dims[1]}x{dims[0]})")

        try:
            while not state.stop:
                # Check if camera change was requested
                with state.lock:
                    if state.camera_change_requested:
                        logger.info("[cam-06] Camera change requested, restarting capture...")
                        break

                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"[cam-06] Frame read failed (ret={ret}), camera disconnected")
                    break

                state.frames_read += 1
                now = time.time()

                # Always serve the latest raw frame to the MJPEG endpoint
                with state.lock:
                    state.raw_frame = frame.copy()
                    if state.annotated is None:
                        state.annotated = frame.copy()

                # Push frame to detector queue (non-blocking, drop if busy)
                if now - state.last_process_at >= PROCESS_EVERY_S:
                    state.last_process_at = now
                    try:
                        _frame_q.put_nowait(frame.copy())
                    except _queue.Full:
                        pass  # detector still busy — skip this frame

                # Pull latest detection results (non-blocking)
                try:
                    det_frame, faces = _result_q.get_nowait()
                except _queue.Empty:
                    # No new result yet — keep showing last annotated frame
                    continue

                # ── Tracking + recognition ──────────────────────────────────
                tracked_ids = _track(faces, state.tracker, now)
                new_tracker: dict[int, dict] = {}
                annotated = det_frame.copy()
                objects: list[dict] = []
                n_auth = 0
                n_intruders = 0

                for idx, (face_id, bbox_px, det_score) in enumerate(tracked_ids):
                    x1, y1, x2, y2 = bbox_px
                    fh, fw = det_frame.shape[:2]
                    bx, by = max(0.0, x1), max(0.0, y1)
                    bw, bh = min(fw - bx, x2 - x1), min(fh - by, y2 - y1)

                    rec = recognizer.identify(faces[idx]["embedding"])
                    status = rec["status"]
                    is_auth = (status == "AUTHORIZED")
                    label = rec["label"]
                    designation = rec.get("designation", "Unauthorized Entity")
                    conf = rec["confidence"]

                    prev = state.tracker.get(face_id)
                    if prev is None or (prev.get("status") != status):
                        _append_alert(status, label, designation, conf)

                    new_tracker[face_id] = {
                        "cx": bx + bw / 2, "cy": by + bh / 2,
                        "w": bw, "h": bh,
                        "label": label,
                        "designation": designation,
                        "status": status,
                        "watchlist": is_auth,
                        "conf": conf,
                        "ts": now,
                    }

                    objects.append({
                        "id": face_id,
                        "cls": "face",
                        "label": label,
                        "designation": designation,
                        "status": status,
                        "watchlist": is_auth,
                        "confidence": conf,
                        "bbox": [round(bx / fw, 4), round(by / fh, 4),
                                 round(bw / fw, 4), round(bh / fh, 4)],
                    })

                    if is_auth:
                        n_auth += 1
                    else:
                        n_intruders += 1

                    _annotate_face(annotated, {
                        "bbox_px": (bx, by, bw, bh),
                        "status": status,
                        "is_auth": is_auth,
                        "label": label,
                        "designation": designation,
                        "confidence": conf,
                    })

                state.tracker = new_tracker
                state.objects = objects
                state.counts = {
                    "faces": len(objects),
                    "authorized": n_auth,
                    "intruders": n_intruders,
                    "watchlist": n_auth,
                    "unknowns": n_intruders,
                }

                with state.lock:
                    state.annotated = annotated

                payload = {
                    "type": "frame",
                    "camera": state.camera_id,
                    "seq": state.seq,
                    "ts": int(time.time() * 1000),
                    "vts": round(time.time() - state.t0, 3),
                    "vfps": 15.0,
                    "efps": round(state.efps, 2),
                    "tracking": True,
                    "first": False,
                    "objects": objects,
                    "counts": dict(state.counts),
                    "alerts": list(state.alerts[:5]),
                }
                state.seq += 1
                _emit(payload)

        finally:
            cap.release()
        logger.info("[cam-06] Webcam stream ended — reopening")



# ── Annotation ────────────────────────────────────────────────────────────────
def _annotate_face(frame: np.ndarray, t: dict) -> None:
    x, y, w, h = (int(v) for v in t["bbox_px"])
    is_auth = t["is_auth"]
    color = WL_COLOR if is_auth else INTRUDER_COLOR
    label = t["label"]
    desig = t["designation"]

    # Box with rounded aesthetic
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

    # Top Status Bar
    tag = f"AUTHORIZED: {label}" if is_auth else "WARNING: INTRUDER"
    (tw, th), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
    by = max(0, y - 18)
    cv2.rectangle(frame, (x, by), (x + tw + 8, by + 16), color, -1)
    cv2.putText(frame, tag, (x + 4, by + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (10, 10, 10), 1, cv2.LINE_AA)

    # Bottom Designation Bar
    sub_tag = desig if is_auth else "UNAUTHORIZED ACCESS"
    (sw, sh), _ = cv2.getTextSize(sub_tag, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
    sy = y + h + 16
    cv2.rectangle(frame, (x, sy - 14), (x + sw + 8, sy + 2), (20, 20, 20), -1)
    cv2.rectangle(frame, (x, sy - 14), (x + sw + 8, sy + 2), color, 1)
    cv2.putText(frame, sub_tag, (x + 4, sy - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1, cv2.LINE_AA)


# ── Frame read helpers for /faces endpoints ───────────────────────────────────
def latest_annotated() -> Optional[np.ndarray]:
    with FACE_PIPELINE.lock:
        f = FACE_PIPELINE.annotated
        return None if f is None else f.copy()


def latest_raw() -> Optional[np.ndarray]:
    with FACE_PIPELINE.lock:
        f = FACE_PIPELINE.raw_frame
        return None if f is None else f.copy()


def placeholder_frame(text: str) -> np.ndarray:
    w, h = FACE_PIPELINE.annotated_dims
    frame = np.zeros((h, w, 3), dtype=np.uint8)
    cv2.putText(frame, f"CAM-06 {text}", (40, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 128), 2)
    return frame


def get_face_pipeline_state() -> dict:
    with FACE_PIPELINE.lock:
        return {
            "camera": "CAM-06",
            "cameraName": "CAM-06 Access Control & Biometric Watchlist",
            "webcam": FACE_PIPELINE.webcam,
            "efps": round(FACE_PIPELINE.efps, 2),
            "counts": dict(FACE_PIPELINE.counts),
            "objects": list(FACE_PIPELINE.objects),
            "alerts": list(FACE_PIPELINE.alerts[:10]),
        }
