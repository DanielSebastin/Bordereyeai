#!/usr/bin/env python3
"""
Quick test to verify the ANPR license plate detector model loads correctly.
Run this from the backend directory to test the model.
"""

from pathlib import Path
import sys

def test_anpr_model():
    print("=" * 60)
    print("Testing ANPR License Plate Detector Model")
    print("=" * 60)
    print()
    
    # Check if model file exists
    model_path = Path("backend/models/license_plate_detector.pt")
    
    if not model_path.exists():
        print("❌ ERROR: Model file not found!")
        print(f"   Expected location: {model_path.absolute()}")
        print()
        print("   Please ensure the model is installed at:")
        print("   backend/models/license_plate_detector.pt")
        return False
    
    print(f"✅ Model file found: {model_path.absolute()}")
    print(f"   Size: {model_path.stat().st_size / (1024*1024):.2f} MB")
    print()
    
    # Try to import ultralytics
    try:
        from ultralytics import YOLO
        print("✅ Ultralytics YOLO imported successfully")
    except ImportError as e:
        print("❌ ERROR: Could not import ultralytics")
        print(f"   {e}")
        print()
        print("   Install with: pip install ultralytics")
        return False
    
    # Try to load the model
    try:
        print()
        print("Loading plate detector model...")
        plate_model = YOLO(str(model_path))
        print("✅ Plate detector model loaded successfully!")
        print()
        
        # Get model info
        print("Model Information:")
        print(f"   Task: {plate_model.task}")
        print(f"   Model type: {type(plate_model).__name__}")
        print()
        
    except Exception as e:
        print("❌ ERROR: Could not load model")
        print(f"   {e}")
        return False
    
    # Summary
    print("=" * 60)
    print("✅ ANPR MODEL TEST PASSED!")
    print("=" * 60)
    print()
    print("The license plate detector is ready to use.")
    print("When you run the backend, cam-02 will use this model")
    print("for accurate plate detection.")
    print()
    print("Expected console output:")
    print('   [cam-02] using dedicated plate detector')
    print()
    
    return True


if __name__ == "__main__":
    success = test_anpr_model()
    sys.exit(0 if success else 1)
