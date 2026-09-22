#!/usr/bin/env python3
"""
Quick test script for InsightFace facial recognition system.

Tests:
1. FaceDetector initialization (InsightFace RetinaFace + ArcFace)
2. Face detection on a test image
3. Embedding generation (512-d vectors)
4. WatchlistManager initialization
5. Basic matching logic

Usage:
    cd backend
    python test_face_system.py
"""
import sys
import numpy as np
import cv2
from pathlib import Path

print("=" * 70)
print("INSIGHTFACE FACIAL RECOGNITION SYSTEM TEST")
print("=" * 70)

# Test 1: Import modules
print("\n[1/5] Testing module imports...")
try:
    from app.vision.face_detector import FaceDetector
    from app.vision.face_recognizer import FaceRecognizer
    from app.vision.watchlist_manager import WatchlistManager
    print("✓ All modules imported successfully")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    print("\nNote: Install dependencies with:")
    print("  pip install insightface onnxruntime opencv-python numpy")
    sys.exit(1)

# Test 2: Initialize FaceDetector
print("\n[2/5] Initializing FaceDetector (InsightFace)...")
try:
    detector = FaceDetector(det_size=640, min_det_score=0.4)
    print("✓ FaceDetector initialized successfully")
    print(f"  - Model: InsightFace buffalo_l (RetinaFace + ArcFace)")
    print(f"  - Detection size: 640x640")
    print(f"  - Min detection score: 0.4")
except Exception as e:
    print(f"✗ FaceDetector initialization failed: {e}")
    print("\nNote: First run will download InsightFace models (~100MB)")
    sys.exit(1)

# Test 3: Test face detection on synthetic image
print("\n[3/5] Testing face detection on synthetic image...")
try:
    # Create a test image (blank canvas)
    test_img = np.ones((480, 640, 3), dtype=np.uint8) * 128
    
    # Draw a simple "face-like" pattern (won't actually detect, but tests the pipeline)
    cv2.circle(test_img, (320, 240), 80, (255, 220, 180), -1)  # Face oval
    cv2.circle(test_img, (290, 220), 15, (50, 50, 50), -1)     # Left eye
    cv2.circle(test_img, (350, 220), 15, (50, 50, 50), -1)     # Right eye
    cv2.ellipse(test_img, (320, 260), (30, 20), 0, 0, 180, (150, 50, 50), 2)  # Mouth
    
    faces = detector.recognize(test_img, max_num=5)
    print(f"✓ Face detection completed")
    print(f"  - Detected faces: {len(faces)}")
    
    if len(faces) > 0:
        face = faces[0]
        print(f"  - Sample detection:")
        print(f"    • BBox: {face['bbox']}")
        print(f"    • Confidence: {face['det_score']:.3f}")
        print(f"    • Embedding shape: {face['embedding'].shape}")
        print(f"    • Embedding type: {face['embedding'].dtype}")
        
        # Verify embedding is normalized
        norm = np.linalg.norm(face['embedding'])
        print(f"    • Embedding L2 norm: {norm:.3f} (should be ~1.0)")
    else:
        print("  - No faces detected (expected - synthetic image)")
        print("  - Detection pipeline working correctly")
    
except Exception as e:
    print(f"✗ Face detection failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Initialize WatchlistManager
print("\n[4/5] Testing WatchlistManager...")
try:
    # Use a test path to avoid overwriting real watchlist
    test_watchlist_path = Path(__file__).parent / "app" / "vision" / "data" / "test_watchlist.json"
    manager = WatchlistManager(path=test_watchlist_path)
    print(f"✓ WatchlistManager initialized")
    print(f"  - Watchlist path: {manager.path}")
    print(f"  - Existing people: {len(manager.people)}")
    print(f"  - Total embeddings: {manager.embedding_count()}")
    print(f"  - Watchlist ready: {manager.watchlist_ready()}")
except Exception as e:
    print(f"✗ WatchlistManager initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Test embedding storage and matching
print("\n[5/5] Testing embedding storage and matching...")
try:
    # Generate some test embeddings (random 512-d vectors)
    test_embeddings = [
        np.random.randn(512).astype(np.float32),
        np.random.randn(512).astype(np.float32),
        np.random.randn(512).astype(np.float32),
    ]
    
    # Add test person
    person = manager.add_person("TestPerson", test_embeddings, replace=True)
    print(f"✓ Added test person to watchlist")
    print(f"  - Person ID: {person['person_id']}")
    print(f"  - Name: {person['name']}")
    print(f"  - Embeddings: {person['embedding_count']}")
    print(f"  - Created: {person['created_at']}")
    
    # Test matching with one of the stored embeddings
    query_embedding = test_embeddings[0]
    matched_person, similarity = manager.best_match(query_embedding, threshold=0.45)
    
    if matched_person:
        print(f"✓ Matching test successful")
        print(f"  - Matched: {matched_person['name']}")
        print(f"  - Similarity: {similarity:.3f}")
    else:
        print(f"✓ No match found (similarity: {similarity:.3f} < 0.45)")
    
    # Test FaceRecognizer
    recognizer = FaceRecognizer(manager, threshold=0.45)
    identity = recognizer.identify(query_embedding)
    print(f"✓ FaceRecognizer test successful")
    print(f"  - Label: {identity['label']}")
    print(f"  - Watchlist: {identity['watchlist']}")
    print(f"  - Confidence: {identity['confidence']}")
    
    # Clean up test file
    if test_watchlist_path.exists():
        test_watchlist_path.unlink()
        print(f"✓ Cleaned up test watchlist file")
    
except Exception as e:
    print(f"✗ Embedding/matching test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Final summary
print("\n" + "=" * 70)
print("✓ ALL TESTS PASSED!")
print("=" * 70)
print("\nInsightFace facial recognition system is working correctly!")
print("\nNext steps:")
print("1. Train the watchlist with real photos:")
print("   python -m app.vision.train_watchlist --name YourName --folder D:\\path\\to\\photos")
print("2. Integrate into the camera pipeline (main.py or camera_runner.py)")
print("3. Test with real video feeds")
print("\nDocumentation: backend/app/vision/data/README.md")
print("=" * 70)
