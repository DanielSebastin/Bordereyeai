#!/usr/bin/env python3
"""Quick WebSocket test to see real-time ANPR data"""
import asyncio
import websockets
import json

async def test_cam02():
    uri = "ws://localhost:8000/ws/analytics"
    
    async with websockets.connect(uri) as websocket:
        # Subscribe to cam-02
        await websocket.send(json.dumps({"camera": "cam-02"}))
        print("[SUBSCRIBED] to cam-02")
        print("[LISTENING] for real-time ANPR detections...")
        print("=" * 70)
        
        frame_count = 0
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                frame_count += 1
                
                # Check for vehicles with plates
                if "objects" in data:
                    vehicles = [obj for obj in data["objects"] if obj.get("cls") in ["car", "truck", "bus", "motorcycle"]]
                    
                    if vehicles:
                        print(f"\n[Frame {frame_count}] {len(vehicles)} vehicle(s) detected")
                        
                        for veh in vehicles:
                            plate = veh.get("plate", "")
                            track_id = veh.get("track_id", "?")
                            cls = veh.get("cls", "vehicle")
                            
                            if plate:
                                print(f"  🚗 {cls.upper()} #{track_id} → PLATE: [{plate}]")
                            else:
                                print(f"  🚗 {cls.upper()} #{track_id} → (no plate yet)")
                
                # Show every 30 frames
                if frame_count % 30 == 0:
                    print(f"[{frame_count} frames processed...]")
                    
            except KeyboardInterrupt:
                print("\n[STOP]")
                break
            except Exception as e:
                print(f"[ERROR] {e}")
                break

if __name__ == "__main__":
    print("=" * 70)
    print("REAL-TIME ANPR TEST - CAM-02 WebSocket Monitor")
    print("=" * 70)
    asyncio.run(test_cam02())
