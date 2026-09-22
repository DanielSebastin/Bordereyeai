"""
Populate Investigation Center with Real Snapshots from MP4 Videos
Extracts detection frames and creates realistic incident records in the database.
"""

import cv2
import base64
import hashlib
import random
import datetime
from pathlib import Path
import sys
import os

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database.db_session import SessionLocal, engine
from app.database.models import (
    Base, SurveillanceEvent, VehicleRecord, AudioAlertRecord,
    Camera, GlobalPerson, PersonSighting
)

# Video files
VIDEO_DIR = Path(__file__).parent.parent
VIDEOS = {
    "cam-01": VIDEO_DIR / "cam1.mp4",
    "cam-02": VIDEO_DIR / "cam2.mp4",
    "cam-03": VIDEO_DIR / "cam3.mp4",
    "cam-04": VIDEO_DIR / "cam4.mp4",
    "cam-05": VIDEO_DIR / "cam5.mp4",
}

# Snapshot output directory
SNAPSHOT_DIR = VIDEO_DIR / "frontend" / "public" / "snapshots"
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

def extract_snapshot(video_path: Path, frame_number: int) -> tuple[bytes, str]:
    """Extract a frame from video and return as JPEG bytes and base64"""
    cap = cv2.VideoCapture(str(video_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Ensure frame number is valid
    frame_number = min(frame_number, total_frames - 1)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        raise ValueError(f"Failed to extract frame {frame_number} from {video_path}")
    
    # Encode as JPEG
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    img_bytes = buffer.tobytes()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    
    return img_bytes, img_base64


def save_snapshot_file(img_bytes: bytes, camera_id: str, incident_id: str) -> str:
    """Save snapshot to public folder and return relative URL"""
    filename = f"{camera_id}_{incident_id}.jpg"
    filepath = SNAPSHOT_DIR / filename
    
    with open(filepath, 'wb') as f:
        f.write(img_bytes)
    
    return f"/snapshots/{filename}"


def create_surveillance_event(db, camera_id: str, event_type: str, severity: str,
                              description: str, snapshot_base64: str, snapshot_url: str,
                              timestamp: datetime.datetime = None) -> SurveillanceEvent:
    """Create a surveillance event with snapshot"""
    if timestamp is None:
        timestamp = datetime.datetime.utcnow()
    
    # Calculate SHA-256 hash of snapshot
    sha256_hash = hashlib.sha256(snapshot_base64.encode()).hexdigest()
    
    event = SurveillanceEvent(
        camera_id=camera_id,
        event_type=event_type,
        severity=severity,
        timestamp=timestamp,
        description=description,
        metadata_json={
            "snapshot_url": snapshot_url,
            "snapshot_base64": snapshot_base64[:100] + "...",  # Store truncated for size
            "hash_sha256": sha256_hash,
            "officer": "AI_OPERATOR",
            "notes": "Automated detection from live surveillance feed"
        }
    )
    
    db.add(event)
    return event


def populate_cameras(db):
    """Ensure all cameras exist in database"""
    cameras = [
        Camera(id="cam-01", name="CAM-01 Gate North", location="North Gate Entry", zone="Sector 1", is_active=True),
        Camera(id="cam-02", name="CAM-02 Vehicle Plaza", location="Vehicle Checkpoint", zone="Sector 2", is_active=True),
        Camera(id="cam-03", name="CAM-03 Low Light Corridor", location="Corridor 1F", zone="Sector 3", is_active=True),
        Camera(id="cam-04", name="CAM-04 Server Room", location="Restricted Vault", zone="Sector 4", is_active=True),
        Camera(id="cam-05", name="CAM-05 Perimeter Fence", location="Western Perimeter", zone="Sector 5", is_active=True),
        Camera(id="CAM-06", name="CAM-06 HQ Facial", location="HQ Command Entry", zone="Sector 6", is_active=True),
    ]
    
    for cam in cameras:
        existing = db.query(Camera).filter(Camera.id == cam.id).first()
        if not existing:
            db.add(cam)
            print(f"✓ Created camera: {cam.id}")
    
    db.commit()


def generate_incidents(db):
    """Generate realistic incident records with actual video snapshots"""
    
    print("\n" + "="*60)
    print("POPULATING INVESTIGATION CENTER WITH REAL VIDEO SNAPSHOTS")
    print("="*60 + "\n")
    
    incidents = []
    
    # CAM-01: Person Detection (Watchlist Match)
    print("📹 CAM-01: Extracting watchlist detection snapshot...")
    try:
        img_bytes, img_base64 = extract_snapshot(VIDEOS["cam-01"], 120)  # Frame at 4 seconds
        snapshot_url = save_snapshot_file(img_bytes, "cam-01", "INC-2026-089")
        
        event = create_surveillance_event(
            db, "cam-01", "watchlist_match", "critical",
            "Watchlist suspect PERSON_001 detected with 99.4% Re-ID similarity",
            img_base64, snapshot_url,
            datetime.datetime.utcnow() - datetime.timedelta(hours=2)
        )
        incidents.append(event)
        print(f"  ✓ Snapshot saved: {snapshot_url}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # CAM-02: Vehicle & ANPR Detection
    print("📹 CAM-02: Extracting vehicle ANPR snapshot...")
    try:
        img_bytes, img_base64 = extract_snapshot(VIDEOS["cam-02"], 240)  # Frame at 8 seconds
        snapshot_url = save_snapshot_file(img_bytes, "cam-02", "INC-2026-090")
        
        event = create_surveillance_event(
            db, "cam-02", "anpr", "high",
            "Unauthorized vehicle detected. Plate: EC65USJ. Confidence: 94.2%",
            img_base64, snapshot_url,
            datetime.datetime.utcnow() - datetime.timedelta(hours=1, minutes=30)
        )
        incidents.append(event)
        
        # Also create vehicle record
        vehicle = VehicleRecord(
            camera_id="cam-02",
            license_plate="EC65USJ",
            vehicle_type="car",
            color="unknown",
            timestamp=event.timestamp,
            crop_path=snapshot_url
        )
        db.add(vehicle)
        print(f"  ✓ Snapshot saved: {snapshot_url}")
        print(f"  ✓ Vehicle record created: EC65USJ")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # CAM-03: Low-light Human Detection
    print("📹 CAM-03: Extracting low-light detection snapshot...")
    try:
        img_bytes, img_base64 = extract_snapshot(VIDEOS["cam-03"], 180)  # Frame at 6 seconds
        snapshot_url = save_snapshot_file(img_bytes, "cam-03", "INC-2026-091")
        
        event = create_surveillance_event(
            db, "cam-03", "person_detection", "medium",
            "Person detected in low-light corridor. Enhanced brightness processing applied.",
            img_base64, snapshot_url,
            datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        )
        incidents.append(event)
        print(f"  ✓ Snapshot saved: {snapshot_url}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # CAM-04: Perimeter Intrusion
    print("📹 CAM-04: Extracting virtual fence intrusion snapshot...")
    try:
        img_bytes, img_base64 = extract_snapshot(VIDEOS["cam-04"], 90)  # Frame at 3 seconds
        snapshot_url = save_snapshot_file(img_bytes, "cam-04", "INC-2026-088")
        
        event = create_surveillance_event(
            db, "cam-04", "intrusion", "critical",
            "Virtual perimeter breach detected. Subject entered restricted zone without authorization.",
            img_base64, snapshot_url,
            datetime.datetime.utcnow() - datetime.timedelta(minutes=45)
        )
        incidents.append(event)
        print(f"  ✓ Snapshot saved: {snapshot_url}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # CAM-05: Crowd Detection
    print("📹 CAM-05: Extracting crowd surveillance snapshot...")
    try:
        img_bytes, img_base64 = extract_snapshot(VIDEOS["cam-05"], 150)  # Frame at 5 seconds
        snapshot_url = save_snapshot_file(img_bytes, "cam-05", "INC-2026-092")
        
        event = create_surveillance_event(
            db, "cam-05", "crowd_detection", "high",
            "Multiple subjects detected at perimeter fence. Elevated surveillance mode activated.",
            img_base64, snapshot_url,
            datetime.datetime.utcnow() - datetime.timedelta(minutes=30)
        )
        incidents.append(event)
        print(f"  ✓ Snapshot saved: {snapshot_url}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # Create additional ANPR detections from CAM-02
    print("\n📹 CAM-02: Creating additional ANPR records...")
    anpr_plates = [
        ("EF10DZT", 180, "INC-2026-093"),
        ("AR65JKV", 300, "INC-2026-094"),
        ("CEEIWIL", 420, "INC-2026-095"),
    ]
    
    for plate, frame, inc_id in anpr_plates:
        try:
            img_bytes, img_base64 = extract_snapshot(VIDEOS["cam-02"], frame)
            snapshot_url = save_snapshot_file(img_bytes, "cam-02", inc_id)
            
            event = create_surveillance_event(
                db, "cam-02", "anpr", "medium",
                f"Vehicle plate detected: {plate}",
                img_base64, snapshot_url,
                datetime.datetime.utcnow() - datetime.timedelta(minutes=random.randint(10, 120))
            )
            
            vehicle = VehicleRecord(
                camera_id="cam-02",
                license_plate=plate,
                vehicle_type="car",
                timestamp=event.timestamp,
                crop_path=snapshot_url
            )
            db.add(vehicle)
            print(f"  ✓ ANPR: {plate} → {snapshot_url}")
        except Exception as e:
            print(f"  ✗ Error extracting {plate}: {e}")
    
    db.commit()
    
    print(f"\n✓ Created {len(incidents) + len(anpr_plates)} surveillance events with snapshots")
    return incidents


def create_mock_audio_alerts(db):
    """Create mock acoustic alerts"""
    print("\n📡 Creating acoustic surveillance alerts...")
    
    audio_alerts = [
        AudioAlertRecord(
            sector="Sector 4 (Western Thar)",
            post_id="POST-04-WEST",
            category="drone",
            event_label="UAV Detection",
            threat_level="CRITICAL",
            confidence=0.92,
            transcript="High-frequency rotor signature detected. BPF: 168 Hz (~5,040 RPM)",
            timestamp=datetime.datetime.utcnow() - datetime.timedelta(minutes=15)
        ),
        AudioAlertRecord(
            sector="Sector 2 (Plaza)",
            post_id="POST-02-PLAZA",
            category="speech",
            event_label="Speech Detection",
            threat_level="MEDIUM",
            confidence=0.85,
            transcript="Conversation detected in restricted zone after hours",
            timestamp=datetime.datetime.utcnow() - datetime.timedelta(minutes=45)
        ),
        AudioAlertRecord(
            sector="Sector 5 (Perimeter)",
            post_id="POST-05-FENCE",
            category="vehicle",
            event_label="Vehicle Engine",
            threat_level="HIGH",
            confidence=0.88,
            transcript="Vehicle engine sound detected near perimeter fence at 2:30 AM",
            timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=3)
        )
    ]
    
    for alert in audio_alerts:
        db.add(alert)
        print(f"  ✓ {alert.event_label} - {alert.sector}")
    
    db.commit()
    print(f"✓ Created {len(audio_alerts)} audio alerts")


def create_person_sightings(db):
    """Create person re-identification sightings"""
    print("\n👤 Creating person re-identification records...")
    
    # Create a global person
    person = GlobalPerson(
        id="PERSON_001",
        first_seen=datetime.datetime.utcnow() - datetime.timedelta(hours=4),
        last_seen=datetime.datetime.utcnow() - datetime.timedelta(hours=2),
        appearance_description="Male, dark jacket, medium height",
        total_sightings=3,
        status="watchlist"
    )
    db.add(person)
    
    # Create sightings across cameras
    sightings = [
        PersonSighting(
            global_person_id="PERSON_001",
            camera_id="cam-01",
            timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=4),
            bbox_x1=0.3, bbox_y1=0.4, bbox_x2=0.5, bbox_y2=0.8,
            detection_confidence=0.95,
            reid_similarity_score=0.998,
            zone_name="North Gate Entry"
        ),
        PersonSighting(
            global_person_id="PERSON_001",
            camera_id="cam-03",
            timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=3, minutes=55),
            bbox_x1=0.4, bbox_y1=0.3, bbox_x2=0.6, bbox_y2=0.7,
            detection_confidence=0.93,
            reid_similarity_score=0.974,
            zone_name="Corridor 1F"
        ),
        PersonSighting(
            global_person_id="PERSON_001",
            camera_id="cam-05",
            timestamp=datetime.datetime.utcnow() - datetime.timedelta(hours=2),
            bbox_x1=0.2, bbox_y1=0.5, bbox_x2=0.4, bbox_y2=0.9,
            detection_confidence=0.91,
            reid_similarity_score=0.962,
            zone_name="Western Perimeter"
        )
    ]
    
    for sighting in sightings:
        db.add(sighting)
        print(f"  ✓ Sighting: {sighting.camera_id} @ {sighting.timestamp.strftime('%H:%M:%S')}")
    
    db.commit()
    print(f"✓ Created person {person.id} with {len(sightings)} sightings")


def main():
    """Main execution"""
    print("\n🚀 Investigation Center Population Script")
    print("=" * 60)
    
    # Create tables if they don't exist
    print("📊 Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database schema ready\n")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Populate cameras
        populate_cameras(db)
        
        # Generate incident records with snapshots
        generate_incidents(db)
        
        # Create audio alerts
        create_mock_audio_alerts(db)
        
        # Create person sightings
        create_person_sightings(db)
        
        print("\n" + "=" * 60)
        print("✅ INVESTIGATION CENTER POPULATED SUCCESSFULLY!")
        print("=" * 60)
        print("\nData created:")
        print("  • Camera configurations: 6")
        print(f"  • Surveillance events: {db.query(SurveillanceEvent).count()}")
        print(f"  • Vehicle/ANPR records: {db.query(VehicleRecord).count()}")
        print(f"  • Audio alerts: {db.query(AudioAlertRecord).count()}")
        print(f"  • Person sightings: {db.query(PersonSighting).count()}")
        print(f"\nSnapshots saved to: {SNAPSHOT_DIR}")
        print("\n✓ Visit http://localhost:3000/investigation-center to view incidents")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
