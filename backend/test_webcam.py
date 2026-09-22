import cv2

print("Testing webcam access...")
print("=" * 50)

for idx in range(10):
    print(f"\nTrying camera index {idx}...")
    
    # Try DSHOW
    print(f"  Backend: DSHOW")
    cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret and frame is not None:
            h, w = frame.shape[:2]
            print(f"  ✓ SUCCESS! Resolution: {w}x{h}")
            cap.release()
            continue
        cap.release()
    
    # Try MSMF
    print(f"  Backend: MSMF")
    cap = cv2.VideoCapture(idx, cv2.CAP_MSMF)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret and frame is not None:
            h, w = frame.shape[:2]
            print(f"  ✓ SUCCESS! Resolution: {w}x{h}")
            cap.release()
            continue
        cap.release()
    
    # Try CAP_ANY
    print(f"  Backend: CAP_ANY")
    cap = cv2.VideoCapture(idx)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret and frame is not None:
            h, w = frame.shape[:2]
            print(f"  ✓ SUCCESS! Resolution: {w}x{h}")
            cap.release()
            continue
        cap.release()
    
    print(f"  ✗ No camera at index {idx}")

print("\n" + "=" * 50)
print("Test complete!")
