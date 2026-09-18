# detect_edge.py
"""
Edge Detection + Adaptive Control (Background Worker version)
- Model chạy nền sau khi đã từng mở
- Chỉ camera ưu tiên (mới nhất) gửi UART
- Tự động xử lý rút/cắm lại UART
"""

import cv2
import time
import threading
from datetime import datetime
from ultralytics import YOLO
from config import INTERSECTIONS, ENVIRONMENT
import serial
import os

# ==================== Shared State ====================
active_cameras = set()
camera_last_active = {}
active_lock = threading.Lock()
current_uart_cam = None

# Background workers
latest_frames = {}          # cam_id → jpeg bytes
worker_running = {}         # cam_id → bool
worker_lock = threading.Lock()

print("[*] Đang khởi tạo detect_edge (Background Worker)...")

# ==================== YOLO ====================
models = {
    "1": YOLO("best.pt"),
    "2": YOLO("best.pt"),
    "3": YOLO("best.pt"),
}

CLASS_NAMES = {0: "Car", 1: "Bus", 2: "Truck", 3: "Motorcycle"}

PCU_FACTORS = {
    0: 1.0,
    1: 2.5,
    2: 2.0,
    3: 0.5,
}

C_MAX = 60

# ==================== UART ====================
UART_PORT = "/dev/ttyUSB0"
BAUD = 115200

srPort = None
is_adaptive = True
last_ack_time = time.time()
uart_lock = threading.Lock()

try:
    srPort = serial.Serial(UART_PORT, BAUD, timeout=0.1)
    time.sleep(2)
    print(f"[UART] Đã kết nối {UART_PORT} @ {BAUD}")
except Exception as e:
    print(f"[UART] Không mở được cổng → Fixed-time: {e}")
    srPort = None
    is_adaptive = False

def ensure_serial():
    global srPort, is_adaptive

    if srPort is not None and srPort.is_open and os.path.exists(UART_PORT):
        return True

    try:
        if srPort is not None:
            srPort.close()
    except:
        pass
    srPort = None

    if os.path.exists(UART_PORT):
        try:
            srPort = serial.Serial(UART_PORT, BAUD, timeout=0.1)
            time.sleep(1.5)
            is_adaptive = True
            print(f"[UART] Đã kết nối lại {UART_PORT} thành công")
            return True
        except Exception as e:
            print(f"[UART] Mở lại cổng thất bại: {e}")
            srPort = None
            is_adaptive = False
            return False

    is_adaptive = False
    return False

def read_from_esp():
    global is_adaptive, last_ack_time

    while True:
        try:
            # Tự mở lại cổng nếu cần
            if not ensure_serial():
                time.sleep(2)
                continue

            if srPort.in_waiting > 0:
                line = srPort.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] [ESP] {line}")

                with uart_lock:
                    if line.startswith("[ACK]"):
                        is_adaptive = True
                        last_ack_time = time.time()
                        print(f"[{timestamp}] → ESP Adaptive")

                    elif line.startswith("[FALLBACK]"):
                        is_adaptive = False
                        print(f"[{timestamp}] ⚠️ ESP FIXED-TIME")

                    elif line.startswith("ENV:"):
                        try:
                            parts = line[4:].split("|")
                            temp = float(parts[0].split(":")[1])
                            humi = float(parts[1].split(":")[1])
                            print(f"Nhiệt độ: {temp}°C | Độ ẩm: {humi}%")
                            ENVIRONMENT["temperature"] = round(temp, 1)
                            ENVIRONMENT["humidity"] = round(humi, 1)
                            ENVIRONMENT["last_update"] = datetime.now().isoformat()
                        except Exception:
                            print("Lỗi parse ENV")
        except Exception as e:
            print(f"[UART] Lỗi đọc: {e}")
            time.sleep(0.5)

        time.sleep(0.05)

threading.Thread(target=read_from_esp, daemon=True).start()
print("[UART] Đã khởi động thread đọc ESP32")

def calc_xor_checksum(data: str) -> str:
    """Tính XOR checksum, trả về 2 ký tự hex (ví dụ: '5A')"""
    cs = 0
    for ch in data:
        cs ^= ord(ch)
    return f"{cs:02X}"

def transmit_data_to_mcu(main_green_time: int, cross_green_time: int):
    if srPort is None or not srPort.is_open:
        return False
    #Create data
    body = f"M:{main_green_time}|C:{cross_green_time}"
    #Calculate checksum
    checksum = calc_xor_checksum(body)
    #Merge to completed data
    packet = f"{body}*{checksum}\n"
    print(f"[UART TX] {packet.strip()}")
    try:
        with uart_lock:
            srPort.write(packet.encode("utf-8"))
            srPort.flush()
        return True
    except Exception as e:
        print(f"[UART] Lỗi gửi: {e}")
        return False

# ==================== Helper ====================
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
        return 30.0, 30.0
    t_main = (q_main / total) * c_max
    t_cross = c_max - t_main
    t_main = max(15.0, min(45.0, t_main))
    t_cross = max(15.0, min(45.0, t_cross))
    return t_main, t_cross

def update_control_local(cam_id, pcu_main, pcu_cross, t_main, t_cross, mode):
    config = INTERSECTIONS.get(cam_id)
    if not config:
        return
    config["pcu_main"] = round(float(pcu_main), 1)
    config["pcu_cross"] = round(float(pcu_cross), 1)
    config["t_green_main"] = int(round(t_main))
    config["t_green_cross"] = int(round(t_cross))
    config["mode"] = mode
    config["last_update"] = time.time()


def print_traffic_stats(cam_id, config):
    global is_adaptive

    if srPort is None or not os.path.exists(UART_PORT):
        is_adaptive = False

    counts_main = config["counts_main"]
    counts_cross = config["counts_cross"]

    q_main = calculate_pcu(counts_main)
    q_cross = calculate_pcu(counts_cross)
    t_main, t_cross = calculate_t_green(q_main, q_cross)

    print("=" * 55)
    print(f" NGÃ TƯ {cam_id} - {config['name']}")
    print(f" Main  → Car:{counts_main[0]} Bus:{counts_main[1]} Truck:{counts_main[2]} Motor:{counts_main[3]}")
    print(f" Cross → Car:{counts_cross[0]} Bus:{counts_cross[1]} Truck:{counts_cross[2]} Motor:{counts_cross[3]}")
    print(f" PCU: {q_main:.1f} / {q_cross:.1f}  |  Đèn xanh: {t_main:.0f}s / {t_cross:.0f}s | Mode: {'adaptive' if is_adaptive else 'fixed'}")
    print("=" * 55)

    current_mode = "adaptive" if is_adaptive else "fixed"
    update_control_local(cam_id, q_main, q_cross, t_main, t_cross, current_mode)

    with active_lock:
        is_allowed = (cam_id == current_uart_cam)

    # ===== CHỈ GỬI UART NẾU ĐÚNG CAMERA ƯU TIÊN =====
    if current_mode == "adaptive" and srPort is not None and os.path.exists(UART_PORT) and is_allowed:
        success = transmit_data_to_mcu(int(round(t_main)), int(round(t_cross)))
        if not success:
            print("[UART] Gửi thất bại → chuyển Fixed")
            is_adaptive = False
    else:
        reasons = []
        if current_mode != "adaptive":
            reasons.append("Fixed-time")
        if srPort is None or not os.path.exists(UART_PORT):
            reasons.append("không có Serial")
        if not is_allowed:
            reasons.append("không phải camera ưu tiên")
        print(f"[UART] Bỏ qua gửi từ cam {cam_id} ({', '.join(reasons)})")


# ==================== Background Worker ====================
def camera_worker(cam_id: str):
    global current_uart_cam, is_adaptive

    config = INTERSECTIONS.get(cam_id)
    if not config:
        return

    print(f"[Worker] Bắt đầu chạy nền cam {cam_id}")

    with active_lock:
        active_cameras.add(cam_id)
        current_uart_cam = cam_id          # ưu tiên UART

    try:
        if not ensure_serial():
            print(f"[Worker] Không có UART → dừng cam {cam_id}")
            return

        cap = cv2.VideoCapture(config["video"])
        if not cap.isOpened():
            print(f"[ERROR] Không mở được video: {config['video']}")
            return

        local_model = models[cam_id]
        track_history = {}
        counted_ids = set()
        last_print_time = time.time()
        PRINT_INTERVAL = 5.0

        while worker_running.get(cam_id, False):
            if not ensure_serial():
                print(f"[Worker] Mất UART → dừng cam {cam_id}")
                update_control_local(cam_id, 0, 0, 30, 30, "fixed")
                is_adaptive = False
                break

            success, frame = cap.read()
            if not success:
                print_traffic_stats(cam_id, config)
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                track_history.clear()
                counted_ids.clear()
                config["counts_main"] = {0: 0, 1: 0, 2: 0, 3: 0}
                config["counts_cross"] = {0: 0, 1: 0, 2: 0, 3: 0}
                continue

            results = local_model.track(
                frame, persist=True, conf=0.25, imgsz=640,
                tracker="bytetrack.yaml", verbose=False
            )

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
                    x1, y1, x2, y2 = map(int, box)
                    cls = int(cls)
                    obj_id = int(obj_id)
                    unique_id = f"{cam_id}_{obj_id}"

                    if cls not in CLASS_NAMES:
                        continue

                    xc = (x1 + x2) // 2
                    yc = (y1 + y2) // 2
                    curr_pt = (xc, yc)

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
                    cv2.circle(frame, curr_pt, 4, (0, 0, 255), -1)
                    label = f"{CLASS_NAMES[cls]} {obj_id} {conf:.2f}"
                    cv2.putText(frame, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                    if unique_id in track_history:
                        prev_pt = track_history[unique_id]
                        if unique_id not in counted_ids:
                            for line in config["main_lines"]:
                                if intersect(prev_pt, curr_pt, line[0], line[1]):
                                    config["counts_main"][cls] += 1
                                    counted_ids.add(unique_id)
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

                            for line in config["cross_lines"]:
                                if intersect(prev_pt, curr_pt, line[0], line[1]):
                                    config["counts_cross"][cls] += 1
                                    counted_ids.add(unique_id)
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

            if time.time() - last_print_time >= PRINT_INTERVAL:
                print_traffic_stats(cam_id, config)
                last_print_time = time.time()

            with active_lock:
                camera_last_active[cam_id] = time.time()

            ret, buffer = cv2.imencode(".jpg", frame)
            if ret:
                with worker_lock:
                    latest_frames[cam_id] = buffer.tobytes()

            time.sleep(0.03)

    finally:
        with worker_lock:
            worker_running[cam_id] = False
            latest_frames.pop(cam_id, None)

        with active_lock:
            active_cameras.discard(cam_id)
            if current_uart_cam == cam_id:
                current_uart_cam = next(iter(active_cameras), None)

        print(f"[Worker] Dừng cam {cam_id} | UART ưu tiên hiện tại: {current_uart_cam}")


def start_camera_worker(cam_id: str):
    """Khởi động worker nếu chưa chạy. Luôn cập nhật camera ưu tiên."""
    global current_uart_cam

    with worker_lock:
        already_running = worker_running.get(cam_id, False)

        if already_running:
            # Chỉ chuyển quyền ưu tiên UART
            with active_lock:
                current_uart_cam = cam_id
            print(f"[Worker] Cam {cam_id} đã chạy nền → chuyển ưu tiên UART")
            return

        worker_running[cam_id] = True

    t = threading.Thread(target=camera_worker, args=(cam_id,), daemon=True)
    t.start()


def generate_frames(cam_id: str):
    """Chỉ chịu trách nhiệm stream frame từ worker nền."""
    config = INTERSECTIONS.get(cam_id)
    if not config:
        return

    # Khởi động / chuyển ưu tiên worker
    start_camera_worker(cam_id)

    # Stream frame mới nhất
    while True:
        with worker_lock:
            frame_bytes = latest_frames.get(cam_id)

        if frame_bytes is None:
            time.sleep(0.05)
            continue

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")

        time.sleep(0.03)


# ==================== Standalone test ====================
if __name__ == "__main__":
    import sys
    cam_id = sys.argv[1] if len(sys.argv) > 1 else "1"
    print(f"[*] Test ngã tư {cam_id} (Ctrl+C để dừng)")
    try:
        for _ in generate_frames(cam_id):
            pass
    except KeyboardInterrupt:
        print("\n[*] Đã dừng")
    finally:
        if srPort and srPort.is_open:
            srPort.close()
