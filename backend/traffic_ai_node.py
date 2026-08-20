import cv2
import time
from datetime import datetime
from ultralytics import YOLO
from config import INTERSECTIONS

print("[*] Đang khởi tạo bộ nhớ AI (Phiên bản Tối ưu RAM cho Edge Node)...")
# Khởi tạo duy nhất 1 mô hình toàn cục để giải phóng RAM cho thiết bị biên
model = YOLO('best.pt')

CLASS_NAMES = {0: 'Car', 1: 'Bus', 2: 'Truck', 3: 'Motorcycle'}

def ccw(A, B, C):
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

def intersect(A, B, C, D):
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

def generate_frames(cam_id: str):
    config = INTERSECTIONS.get(cam_id)
    if not config:
        return
        
    cap = cv2.VideoCapture(config["video"])
    
    # Không gian bộ nhớ cục bộ cho thuật toán đếm xe
    track_history = {} 
    counted_ids = set()
    
    frame_counter = 0
    FRAME_SKIP = 1

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            track_history.clear() 
            counted_ids.clear()
            continue 

        frame_counter += 1
        if frame_counter % FRAME_SKIP != 0:
            continue

        results = model.track(frame, persist=True, conf=0.25, imgsz=640, tracker="bytetrack.yaml", verbose=False)

        for line in config["main_lines"]:
            cv2.line(frame, line[0], line[1], (0, 255, 0), 2)
        for line in config["cross_lines"]:
            cv2.line(frame, line[0], line[1], (255, 0, 0), 2)

        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            clss = results[0].boxes.cls.cpu().numpy()
            ids = results[0].boxes.id.cpu().numpy()
            confs = results[0].boxes.conf.cpu().numpy()

            for box, cls, obj_id, conf in zip(boxes, clss, ids, confs):
                x1, y1, x2, y2 = box
                cls = int(cls)
                obj_id = int(obj_id)
                unique_id = f"{cam_id}_{obj_id}"

                if cls in CLASS_NAMES:
                    xc = int((x1 + x2) / 2)
                    yc = int((y1 + y2) / 2)
                    curr_pt = (xc, yc)

                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (255, 255, 0), 2)
                    cv2.circle(frame, curr_pt, 4, (0, 0, 255), -1)
                    
                    label = f"{CLASS_NAMES[cls]} {obj_id} {conf:.2f}"
                    cv2.putText(frame, label, (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                    if unique_id in track_history:
                        prev_pt = track_history[unique_id]
                        
                        if unique_id not in counted_ids:
                            # --- KIỂM TRA TRỤC CHÍNH ---
                            for line in config["main_lines"]:
                                if intersect(prev_pt, curr_pt, line[0], line[1]):
                                    config["counts_main"][cls] += 1
                                    counted_ids.add(unique_id)
                                    cv2.line(frame, line[0], line[1], (0, 0, 255), 6)
                                    
                                    now = datetime.now().strftime("%H:%M:%S")
                                    event = {
                                        "id": int(time.time() * 1000) + obj_id,
                                        "time": now,
                                        "message": f"Phát hiện {CLASS_NAMES[cls]} qua Trục Chính",
                                        "type": "vehicle",
                                        "vehicle_type": CLASS_NAMES[cls],
                                        "conf": f"{conf:.2f}"
                                    }
                                    config["events"].insert(0, event)
                                    break
                            
                            # --- KIỂM TRA TRỤC PHỤ ---
                            for line in config["cross_lines"]:
                                if intersect(prev_pt, curr_pt, line[0], line[1]):
                                    config["counts_cross"][cls] += 1
                                    counted_ids.add(unique_id)
                                    cv2.line(frame, line[0], line[1], (0, 0, 255), 6)
                                    
                                    now = datetime.now().strftime("%H:%M:%S")
                                    event = {
                                        "id": int(time.time() * 1000) + obj_id,
                                        "time": now,
                                        "message": f"Phát hiện {CLASS_NAMES[cls]} qua Trục Phụ",
                                        "type": "vehicle",
                                        "vehicle_type": CLASS_NAMES[cls],
                                        "conf": f"{conf:.2f}"
                                    }
                                    config["events"].insert(0, event)
                                    break

                            if len(config["events"]) > 15:
                                config["events"].pop()

                    track_history[unique_id] = curr_pt

        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')