# import cv2
# import numpy as np
# from ultralytics import YOLO
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import StreamingResponse
# from pydantic import BaseModel
# import jwt
# from datetime import datetime, timedelta
# import time
# app = FastAPI(title="ITS Core API - Multi Camera")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173"], 
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ==========================================
# # CẤU HÌNH BẢO MẬT JWT LOGIN
# # ==========================================
# SECRET_KEY = "its_core_secret_key_super_safe"
# ALGORITHM = "HS256"

# USERS = {
#     "admin@gmail.com": "admin123",
#     "root@gmail.com": "root123"
# }

# class LoginRequest(BaseModel):
#     email: str
#     password: str

# @app.post("/api/login")
# async def login(request: LoginRequest):
#     if request.email in USERS and USERS[request.email] == request.password:
#         # Thời gian hết hạn của token là 24 giờ
#         expire = datetime.utcnow() + timedelta(hours=24)
#         payload = {"sub": request.email, "exp": expire, "role": "admin"}
#         token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
#         return {"access_token": token, "token_type": "bearer", "message": "Đăng nhập thành công"}
#     raise HTTPException(status_code=401, detail="Tài khoản hoặc mật khẩu không chính xác")

# # ==========================================
# # CẤU HÌNH 3 NGÃ TƯ (MULTI-CAMERA CONFIG)
# # ==========================================
# INTERSECTIONS = {
#     "1": {
#         "name": "Ngã tư Điện Biên Phủ",
#         "video": "videos/video_int_01.mp4",
#         "main_lines": [[(268, 352), (524, 192)], [(42, 165), (256, 71)]],
#         "cross_lines": [[(158, 345), (21, 216)], [(342, 67), (513, 145)]],
#         "counts_main": {0: 0, 1: 0, 2: 0, 3: 0},
#         "counts_cross": {0: 0, 1: 0, 2: 0, 3: 0},
#         "events": []
#     },
#     "2": {
#         "name": "Ngã tư Phạm Văn Đồng",
#         "video": "videos/video_int_02.mp4",
#         "main_lines": [[(817, 661), (1132, 279)], [(59, 291), (375, 106)]],
#         "cross_lines": [[(51, 454), (584, 698)], [(567, 88), (1093, 239)]],
#         "counts_main": {0: 0, 1: 0, 2: 0, 3: 0},
#         "counts_cross": {0: 0, 1: 0, 2: 0, 3: 0},
#         "events": []
#     },
#     "3": {
#         "name": "Ngã tư Nguyễn Hữu Cảnh",
#         "video": "videos/video_int_03.mp4",
#         "main_lines": [[(1068, 327), (767, 720)], [(365, 251), (640, 196)]],
#         "cross_lines": [[(175, 397), (616, 720)], [(799, 204), (1050, 318)]],
#         "counts_main": {0: 0, 1: 0, 2: 0, 3: 0},
#         "counts_cross": {0: 0, 1: 0, 2: 0, 3: 0},
#         "events": []
#     }
# }

# class_names = {0: 'Car', 1: 'Bus', 2: 'Truck', 3: 'Motorcycle'}

# # ==========================================
# # KHỞI TẠO AI
# # ==========================================
# print("[*] Đang khởi tạo mô hình YOLO26 vào bộ nhớ...")
# model = YOLO('best.pt') 

# print("[*] Đang Warm-up AI (Xóa bỏ delay khi khởi động)...")
# dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)
# model.track(dummy_frame, persist=True, verbose=False)
# print("[*] Warm-up hoàn tất! Server đã sẵn sàng.")

# def ccw(A, B, C):
#     return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

# def intersect(A, B, C, D):
#     return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

# def generate_frames(cam_id: str):
#     config = INTERSECTIONS.get(cam_id)
#     if not config:
#         return
        
#     cap = cv2.VideoCapture(config["video"])
#     track_history = {} 
#     counted_ids = set()
    
#     frame_counter = 0
#     FRAME_SKIP = 2  

#     while cap.isOpened():
#         success, frame = cap.read()
#         if not success:
#             cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Lặp lại video
#             continue 

#         frame_counter += 1
#         if frame_counter % FRAME_SKIP != 0:
#             continue

#         results = model.track(frame, persist=True, conf=0.35, tracker="bytetrack.yaml", verbose=False)

#         for line in config["main_lines"]:
#             cv2.line(frame, line[0], line[1], (0, 255, 0), 2)
#         for line in config["cross_lines"]:
#             cv2.line(frame, line[0], line[1], (255, 0, 0), 2)

#         if results[0].boxes.id is not None:
#             boxes = results[0].boxes.xyxy.cpu().numpy()
#             clss = results[0].boxes.cls.cpu().numpy()
#             ids = results[0].boxes.id.cpu().numpy()
#             confs = results[0].boxes.conf.cpu().numpy()

#             for box, cls, obj_id, conf in zip(boxes, clss, ids, confs):
#                 x1, y1, x2, y2 = box
#                 cls = int(cls)
#                 obj_id = int(obj_id)

#                 if cls in class_names:
#                     xc = int((x1 + x2) / 2)
#                     yc = int((y1 + y2) / 2)
#                     curr_pt = (xc, yc)

#                     cv2.circle(frame, curr_pt, 4, (0, 0, 255), -1)
#                     cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 255), 1)
#                     cv2.putText(frame, f"{class_names[cls]} {obj_id}", (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 1)

#                     if obj_id in track_history:
#                         prev_pt = track_history[obj_id]
                        
#                         if obj_id not in counted_ids:
#                             # --- MAIN AXIS ---
#                             for line in config["main_lines"]:
#                                 if intersect(prev_pt, curr_pt, line[0], line[1]):
#                                     config["counts_main"][cls] += 1
#                                     counted_ids.add(obj_id)
#                                     cv2.line(frame, line[0], line[1], (0, 0, 255), 6)
                                    
#                                     now = datetime.now().strftime("%H:%M:%S")
#                                     event = {
#                                         "id": int(time.time() * 1000) + obj_id,
#                                         "time": now,
#                                         "message": f"Phát hiện {class_names[cls]} qua Trục Chính",
#                                         "type": "vehicle",
#                                         "vehicle_type": class_names[cls],
#                                         "conf": f"{conf:.2f}"
#                                     }
#                                     config["events"].insert(0, event)
#                                     break
                            
#                             # --- CROSS AXIS ---
#                             for line in config["cross_lines"]:
#                                 if intersect(prev_pt, curr_pt, line[0], line[1]):
#                                     config["counts_cross"][cls] += 1
#                                     counted_ids.add(obj_id)
#                                     cv2.line(frame, line[0], line[1], (0, 0, 255), 6)
                                    
#                                     now = datetime.now().strftime("%H:%M:%S")
#                                     event = {
#                                         "id": int(time.time() * 1000) + obj_id,
#                                         "time": now,
#                                         "message": f"Phát hiện {class_names[cls]} qua Trục Phụ",
#                                         "type": "vehicle",
#                                         "vehicle_type": class_names[cls],
#                                         "conf": f"{conf:.2f}"
#                                     }
#                                     config["events"].insert(0, event)
#                                     break
                                    
#                             if len(config["events"]) > 15:
#                                 config["events"].pop()

#                     track_history[obj_id] = curr_pt

#         cv2.putText(frame, "MAIN AXIS (Green)", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
#         y_off = 60
#         for c_id, name in class_names.items():
#             cv2.putText(frame, f"{name}: {config['counts_main'][c_id]}", (20, y_off), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
#             y_off += 25
            
#         cv2.putText(frame, "CROSS AXIS (Blue)", (20, y_off + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
#         y_off += 50
#         for c_id, name in class_names.items():
#             cv2.putText(frame, f"{name}: {config['counts_cross'][c_id]}", (20, y_off), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
#             y_off += 25

#         ret, buffer = cv2.imencode('.jpg', frame)
#         frame_bytes = buffer.tobytes()

#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# # API ĐỘNG NHẬN ID NGÃ TƯ
# @app.get("/api/video_feed/{intersection_id}")
# def video_feed(intersection_id: str):
#     if intersection_id not in INTERSECTIONS:
#         raise HTTPException(status_code=404, detail="Không tìm thấy ngã tư này")
#     return StreamingResponse(generate_frames(intersection_id), media_type="multipart/x-mixed-replace; boundary=frame")

# @app.get("/api/traffic_stats/{intersection_id}")
# def get_traffic_stats(intersection_id: str):
#     if intersection_id not in INTERSECTIONS:
#         raise HTTPException(status_code=404, detail="Không tìm thấy ngã tư này")
#     config = INTERSECTIONS[intersection_id]
#     return {
#         "name": config["name"],
#         "counts_main": config["counts_main"],
#         "counts_cross": config["counts_cross"],
#         "events": config["events"]
#     }
# main.py
# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from config import INTERSECTIONS, ENVIRONMENT
from auth import LoginRequest, verify_login
from detect_edge import generate_frames, active_cameras
from datetime import datetime

app = FastAPI(title="ITS Core API - Edge Node")

# Cho phép Frontend từ laptop
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Dev: cho tất cả. Production nên giới hạn IP laptop
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/login")
async def login(request: LoginRequest):
    return verify_login(request)

@app.get("/api/video_feed/{intersection_id}")
def video_feed(intersection_id: str):
    if intersection_id not in INTERSECTIONS:
        raise HTTPException(status_code=404, detail="Không tìm thấy ngã tư này")
    return StreamingResponse(
        generate_frames(intersection_id),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/api/traffic_stats/{intersection_id}")
def get_traffic_stats(intersection_id: str):
    if intersection_id not in INTERSECTIONS:
        raise HTTPException(status_code=404, detail="Không tìm thấy ngã tư này")
    config = INTERSECTIONS[intersection_id]
    return {
        "name": config["name"],
        "counts_main": config["counts_main"],
        "counts_cross": config["counts_cross"],
        "events": config["events"],
        "pcu_main": config.get("pcu_main", 0.0),
        "pcu_cross": config.get("pcu_cross", 0.0),
        "t_green_main": config.get("t_green_main", 30),
        "t_green_cross": config.get("t_green_cross", 30),
        "mode": config.get("mode", "fixed"),
        "last_update": config.get("last_update"),
    }

@app.get("/api/environment")
def get_environment():
    return ENVIRONMENT

@app.post("/api/update_control/{intersection_id}")
def update_control(intersection_id: str, data: dict):
    # Giữ lại để tương thích (detect_edge đã cập nhật trực tiếp)
    if intersection_id not in INTERSECTIONS:
        raise HTTPException(status_code=404, detail="Không tìm thấy ngã tư")
    config = INTERSECTIONS[intersection_id]
    config["pcu_main"] = data.get("pcu_main", config.get("pcu_main", 0.0))
    config["pcu_cross"] = data.get("pcu_cross", config.get("pcu_cross", 0.0))
    config["t_green_main"] = data.get("t_green_main", config.get("t_green_main", 30))
    config["t_green_cross"] = data.get("t_green_cross", config.get("t_green_cross", 30))
    config["mode"] = data.get("mode", config.get("mode", "fixed"))
    config["last_update"] = datetime.now().timestamp()
    return {"status": "ok"}

@app.post("/api/update_environment")
def update_environment(data: dict):
    ENVIRONMENT["temperature"] = data.get("temperature")
    ENVIRONMENT["humidity"] = data.get("humidity")
    ENVIRONMENT["last_update"] = datetime.now().isoformat()
    return {"status": "ok"}

@app.get("/api/overview_stats")
def get_overview_stats():
    total_pcu = 0
    total_vehicles = 0
    for config in INTERSECTIONS.values():
        motos = config["counts_main"].get(3, 0) + config["counts_cross"].get(3, 0)
        cars = config["counts_main"].get(0, 0) + config["counts_cross"].get(0, 0)
        trucks = config["counts_main"].get(2, 0) + config["counts_cross"].get(2, 0)
        buses = config["counts_main"].get(1, 0) + config["counts_cross"].get(1, 0)
        pcu = (motos * 0.5) + (cars * 1) + (trucks * 2) + (buses * 2.5)
        total_pcu += pcu
        total_vehicles += (motos + cars + trucks + buses)

    return {
        "total_intersections": len(INTERSECTIONS),
        "active_nodes": len(active_cameras),
        "active_cameras": list(active_cameras),
        "total_pcu": round(total_pcu),
        "total_vehicles_24h": total_vehicles,
        "system_status": "Ổn định" if True else "Mất kết nối",
    }
