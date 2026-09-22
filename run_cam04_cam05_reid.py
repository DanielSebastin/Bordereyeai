#!/usr/bin/env python3
"""
Quick Re-ID runner for CAM-04 and CAM-05
Processes cam4.mp4 and cam5.mp4 with person Re-ID tracking
"""
import os
import sys
import cv2
import datetime
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from database.db_session import SessionLocal, init_db
from database.models import Camera, GlobalPerson, PersonSighting
from reid_engine.pipeline import MultiCameraReIDPipeline

def run_reid_cams():
    print("=" * 75)
    print(" CAM-04 & CAM-05: MULTI-CAMERA PERSON RE-ID")
    print(" Processing cam4.mp4 and cam5.mp4 with cross-camera tracking")
    print(" Press Ctrl+C to stop")
    print("=" * 75)

    init_db()
    db = SessionLocal()
    pipeline = MultiCameraReIDPipeline()

    # Open video files
    cap4 = cv2.VideoCapture("cam4.mp4")
    cap5 = cv2.VideoCapture("cam5.mp4")

    if not cap4.isOpened():
        print("[ERROR] Could not open cam4.mp4")
        return
    
    if not cap5.isOpened():
        print("[ERROR] Could not open cam5.mp4")
        return

    print("[OK] Video files loaded successfully")
    
    frame_count = 0
    start_time = time.time()

    try:
        while True:
            # Read frames
            ret4, frame4 = cap4.read()
            ret5, frame5 = cap5.read()

            # Loop videos
            if not ret4:
                cap4.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret4, frame4 = cap4.read()
            
            if not ret5:
                cap5.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret5, frame5 = cap5.read()

            if not ret4 or not ret5:
                break

            now = datetime.datetime.utcnow()
            frame_count += 1

            # Process CAM-04 with Re-ID
            persons_cam4 = []
            if frame4 is not None:
                try:
                    persons_cam4 = pipeline.process_frame(db, frame4, camera_id="cam-04", timestamp=now)
                except Exception as e:
                    if frame_count == 1:
                        print(f"[WARN] Re-ID pipeline error (will continue without DB): {e}")
                    persons_cam4 = []
                
                # Draw results on frame
                for p in persons_cam4:
                    if 'bbox' in p:
                        x1, y1, x2, y2 = map(int, p['bbox'])
                        global_id = p.get('global_person_id', 'Unknown')
                        color = (0, 255, 0) if global_id != 'Unknown' else (0, 0, 255)
                        cv2.rectangle(frame4, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(frame4, f"ID:{global_id}", (x1, y1-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                cv2.putText(frame4, "CAM-04 Re-ID", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

            # Process CAM-05 with Re-ID  
            if frame5 is not None:
                persons_cam5 = pipeline.process_frame(db, frame5, camera_id="cam-05", timestamp=now)
                
                # Draw results on frame
                for p in persons_cam5:
                    if 'bbox' in p:
                        x1, y1, x2, y2 = map(int, p['bbox'])
                        global_id = p.get('global_person_id', 'Unknown')
                        color = (0, 255, 0) if global_id != 'Unknown' else (0, 0, 255)
                        cv2.rectangle(frame5, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(frame5, f"ID:{global_id}", (x1, y1-10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                cv2.putText(frame5, "CAM-05 Re-ID", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

            # Display side by side
            if frame4 is not None and frame5 is not None:
                # Resize for display
                h4, w4 = frame4.shape[:2]
                h5, w5 = frame5.shape[:2]
                
                # Make same height
                if h4 != h5:
                    frame5 = cv2.resize(frame5, (int(w5 * h4 / h5), h4))
                
                combined = np.hstack([frame4, frame5])
                combined = cv2.resize(combined, (1280, 480))
                
                # Show FPS
                elapsed = time.time() - start_time
                fps = frame_count / elapsed if elapsed > 0 else 0
                cv2.putText(combined, f"FPS: {fps:.1f}", (10, 470),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                
                cv2.imshow("CAM-04 & CAM-05 Person Re-ID", combined)

            # Exit on 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # Print progress every 30 frames
            if frame_count % 30 == 0:
                elapsed = time.time() - start_time
                fps = frame_count / elapsed
                print(f"[Frame {frame_count}] FPS: {fps:.1f} | CAM-04: {len(persons_cam4)} persons | CAM-05: {len(persons_cam5)} persons")

    except KeyboardInterrupt:
        print("\n[STOP] User interrupted")
    finally:
        cap4.release()
        cap5.release()
        cv2.destroyAllWindows()
        db.close()
        
        elapsed = time.time() - start_time
        fps = frame_count / elapsed if elapsed > 0 else 0
        print(f"\n[DONE] Processed {frame_count} frames in {elapsed:.1f}s ({fps:.1f} FPS)")

if __name__ == "__main__":
    run_reid_cams()
