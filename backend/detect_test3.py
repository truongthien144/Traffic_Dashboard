#!/usr/bin/env python3
"""
detect_test2.py
- Nhận diện phương tiện bằng YOLO
- Tính PCU và thời gian đèn xanh thích nghi
- Gửi xuống ESP32 qua UART
- Đọc phản hồi từ ESP32 (ACK / FALLBACK)
"""

import cv2
import time
import threading
from datetime import datetime
from ultralytics import YOLO
from config import INTERSECTIONS
import serial
import requests

print("[*] Đang khởi tạo bộ nhớ độc lập cho 3 ngã tư...")

# ==================== YOLO ====================
models = {
    "1": YOLO('best.pt'),
    "2": YOLO('best.pt'),
    "3": YOLO('best.pt')
}

CLASS_NAMES = {0: 'Car', 1: 'Bus', 2: 'Truck', 3: 'Motorcycle'}

PCU_FACTORS = {
    0: 1.0,   # Car
    1: 2.5,   # Bus
    2: 2.0,   # Truck
    3: 0.5    # Motorcycle
}

C_MAX = 60  # Chu kỳ tối đa (giây)
# ==================== WEB ====================
DASHBOARD_URL = "http://192.168.101.8:8000"

def push_control_to_dashboard(cam_id, pcu_main, pcu_cross, t_main, t_cross, mode="adaptive"):
    try:
        requests.post(
            f"{DASHBOARD_URL}/api/update_control/{cam_id}",
            json={
                "pcu_main": round(float(pcu_main), 1),
                "pcu_cross": round(float(pcu_cross), 1),
                "t_green_main": int(round(t_main)),
                "t_green_cross": int(round(t_cross)),
                "mode": mode
            },
            timeout=3.0
        )
    except Exception as e:
        print(f"[Dashboard] Lỗi gửi control: {e}")


def push_environment_to_dashboard(temp, humi):
    try:
        requests.post(
            f"{DASHBOARD_URL}/api/update_environment",
            json={
                "temperature": round(float(temp), 1),
                "humidity": round(float(humi), 1)
            },
            timeout=1.0
        )
    except Exception as e:
        print(f"[Dashboard] Lỗi gửi ENV: {e}")
# ==================== UART ====================
UART_PORT = "/dev/ttyUSB0"   # Đổi thành /dev/serial0 hoặc /dev/ttyAMA0 nếu dùng GPIO UART
BAUD = 115200

srPort = None
is_adaptive = True
last_ack_time = time.time()
uart_lock = threading.Lock()

try:
    srPort = serial.Serial(UART_PORT, BAUD, timeout=0.1)
    time.sleep(2)  # đợi ESP32 ổn định
    print(f"[UART] Đã kết nối {UART_PORT} @ {BAUD}")
except Exception as e:
    print(f"[UART] Không mở được cổng: {e}")
    srPort = None


def read_from_esp():
    """Thread đọc liên tục phản hồi từ ESP32"""
    global is_adaptive, last_ack_time

    while True:
        try:
            if srPort is None or not srPort.is_open:
                time.sleep(1)
                continue

            if srPort.in_waiting > 0:
                line = srPort.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue

                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"[{timestamp}] [ESP] {line}")

                with uart_lock:
                    if line.startswith("[ACK]"):
                        is_adaptive = True
                        last_ack_time = time.time()
                        print(f"[{timestamp}] → ESP đang ở chế độ Adaptive")

                    elif line.startswith("[FALLBACK]"):
                        is_adaptive = False
                        print(f"[{timestamp}] ⚠️  ESP đã chuyển sang FIXED-TIME!")

                    elif line.startswith("[INVALID]") or line.startswith("[PARSE FAIL]"):
                        print(f"[{timestamp}] ⚠️  Gói tin gửi lên bị lỗi")
                    elif line.startswith("ENV:"):
                        try:
                         parts = line[4:].split("|")
                         temp = float(parts[0].split(":")[1])
                         humi = float(parts[1].split(":")[1])
                         print(f"Nhiệt độ: {temp}°C | Độ ẩm: {humi}%")
                         # → Gửi tiếp lên Dashboard ở code khác
                         push_environment_to_dashboard(temp, humi)
                        except:
                         print("Lỗi parse ENV")
        except Exception as e:
         print(f"[UART] Lỗi đọc: {e}")
         time.sleep(0.5)

        time.sleep(0.05)


# Khởi động thread đọc ngay khi chạy
if srPort is not None:
    reader_thread = threading.Thread(target=read_from_esp, daemon=True)
    reader_thread.start()
    print("[UART] Đã khởi động thread đọc phản hồi từ ESP32")


def transmit_data_to_mcu(main_green_time, cross_green_time):
    """Gửi thời gian đèn xanh xuống ESP32 theo protocol M:xx|C:yy"""
    global srPort

    if srPort is None or not srPort.is_open:
        print("[UART] Error: Serial port not initialized. Cannot transmit data.")
        return False

    packet = f"M:{main_green_time}|C:{cross_green_time}\n"
    print(f"[UART TX] Transmitting to MCU: {packet.strip()}")

    try:
        srPort.write(packet.encode('utf-8'))
        srPort.flush()
        print("[UART] Data transmission successful.")
        return True
    except Exception as e:
        print(f"[UART] Lỗi khi gửi: {e}")
        return False


# ==================== HÀM HỖ TRỢ ====================
def ccw(A, B, C):
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])


def intersect(A, B, C, D):
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)


def calculate_pcu(counts_dict):
    total = 0.0
    for cls_id, count in counts_dict.items():
        total += PCU_FACTORS.get(cls_id, 1.0) * count
    return total


def calculate_t_green(q_main, q_cross, c_max=C_MAX):
    total = q_main + q_cross
    if total == 0:
        # Fallback / Night Mode
        return 30.0, 30.0

    t_main = (q_main / total) * c_max
    t_cross = c_max - t_main

    # Clamp [15, 45]
    t_main = max(15.0, min(45.0, t_main))
    t_cross = max(15.0, min(45.0, t_cross))
    return t_main, t_cross


def print_traffic_stats(cam_id, config):
    counts_main = config["counts_main"]
    counts_cross = config["counts_cross"]

    q_main = calculate_pcu(counts_main)
    q_cross = calculate_pcu(counts_cross)
    t_main, t_cross = calculate_t_green(q_main, q_cross)

    print("=" * 55)
    print(f" TỔNG KẾT TẢI LƯỢNG NGÃ TƯ {cam_id} ({config['name']})")
    print("=" * 55)
    print("[*] TRỤC CHÍNH (MAIN AXIS):")
    print(f"    - Car: {counts_main[0]}")
    print(f"    - Bus: {counts_main[1]}")
    print(f"    - Truck: {counts_main[2]}")
    print(f"    - Motorcycle: {counts_main[3]}")
    print()
    print("[*] TRỤC PHỤ (CROSS AXIS):")
    print(f"    - Car: {counts_cross[0]}")
    print(f"    - Bus: {counts_cross[1]}")
    print(f"    - Truck: {counts_cross[2]}")
    print(f"    - Motorcycle: {counts_cross[3]}")
    print("=" * 55)
    print(" KẾT QUẢ ĐIỀU KHIỂN PHA ĐÈN THÍCH NGHI")
    print("=" * 55)
    print(f"  - Tải lượng trục Main:  {q_main:.1f} PCU")
    print(f"  - Tải lượng trục Cross: {q_cross:.1f} PCU")
    print(f"  => THỜI GIAN ĐÈN XANH Main:  {t_main:.1f} Giây")
    print(f"  => THỜI GIAN ĐÈN XANH Cross: {t_cross:.1f} Giây")
    print("=" * 55)
    print()

    # ===== Gửi xuống ESP32 =====
    # Chỉ gửi khi đang Adaptive (hoặc bạn muốn luôn gửi thì bỏ if)
    with uart_lock:
        current_mode = is_adaptive
        mode_str = "adaptive" if current_mode else "fixed"
        push_control_to_dashboard(cam_id, q_main, q_cross, t_main, t_cross, mode=mode_str)
    if current_mode:
        transmit_data_to_mcu(int(round(t_main)), int(round(t_cross)))
    else:
        print("[UART] Đang ở FIXED-TIME → tạm không gửi Adaptive")


def generate_frames(cam_id: str):
    config = INTERSECTIONS.get(cam_id)
    if not config:
        return

    cap = cv2.VideoCapture(config["video"])
    local_model = models[cam_id]

    track_history = {}
    counted_ids = set()
    frame_counter = 0
    FRAME_SKIP = 1

    last_print_time = time.time()
    PRINT_INTERVAL = 5.0  # giây

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            # Video loop lại → in thống kê + reset
            print_traffic_stats(cam_id, config)
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            track_history.clear()
            counted_ids.clear()
            config["counts_main"] = {0: 0, 1: 0, 2: 0, 3: 0}
            config["counts_cross"] = {0: 0, 1: 0, 2: 0, 3: 0}
            continue

        frame_counter += 1
        if frame_counter % FRAME_SKIP != 0:
            continue

        results = local_model.track(
            frame, persist=True, conf=0.25, imgsz=640,
            tracker="bytetrack.yaml", verbose=False
        )

        # Vẽ line
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
                    cv2.putText(frame, label, (int(x1), int(y1)-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                    if unique_id in track_history:
                        prev_pt = track_history[unique_id]

                        if unique_id not in counted_ids:
                            # --- TRỤC CHÍNH ---
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

                            # --- TRỤC PHỤ ---
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

                            # Giới hạn 15 sự kiện
                            if len(config["events"]) > 15:
                                config["events"].pop()

                    track_history[unique_id] = curr_pt

        # In thống kê định kỳ
        current_time = time.time()
        if current_time - last_print_time >= PRINT_INTERVAL:
            print_traffic_stats(cam_id, config)
            last_print_time = current_time

        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


# ==================== CHẠY TRỰC TIẾP ====================
if __name__ == "__main__":
    import sys
    cam_id = sys.argv[1] if len(sys.argv) > 1 else "1"

    print(f"[*] Bắt đầu test ngã tư {cam_id}...")
    print("[*] Nhấn Ctrl+C để dừng.\n")

    try:
        for _ in generate_frames(cam_id):
            pass
    except KeyboardInterrupt:
        print("\n[*] Đã dừng bởi người dùng.")
        config = INTERSECTIONS.get(cam_id)
        if config:
            print_traffic_stats(cam_id, config)
    finally:
        if srPort is not None and srPort.is_open:
            srPort.close()
            print("[UART] Đã đóng Serial.")
