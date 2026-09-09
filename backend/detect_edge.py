# detect_edge.py
"""
Edge Detection + Adaptive Control
- Chạy trên Raspberry Pi
- YOLO tracking + đếm xe
- Tính PCU + thời gian đèn xanh thích nghi
- Stream video đã annotate
- Gửi UART xuống ESP32
- Cập nhật trực tiếp vào INTERSECTIONS (đồng bộ với Dashboard)
"""

import cv2
import time
import threading
from datetime import datetime
from ultralytics import YOLO
from config import INTERSECTIONS, ENVIRONMENT
import serial

active_cameras = set()
camera_last_active = {}
active_lock = threading.Lock()
current_uart_cam = None
print("[*] Đang khởi tạo detect_edge cho 3 ngã tư...")

# ==================== YOLO ====================
models = {
    "1": YOLO("best.pt"),
    "2": YOLO("best.pt"),
    "3": YOLO("best.pt"),
}

CLASS_NAMES = {0: "Car", 1: "Bus", 2: "Truck", 3: "Motorcycle"}

PCU_FACTORS = {
    0: 1.0,   # Car
    1: 2.5,   # Bus
    2: 2.0,   # Truck
    3: 0.5,   # Motorcycle
}

C_MAX = 60  # Chu kỳ tối đa (giây)

# ==================== UART ====================
UART_PORT = "/dev/ttyUSB0"   # Đổi nếu cần: /dev/serial0 hoặc /dev/ttyAMA0
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
    print(f"[UART] Không mở được cổng → chạy Fixed-time: {e}")
    srPort = None
    is_adaptive = False


def read_from_esp():
    """Thread đọc phản hồi từ ESP32"""
    global is_adaptive, last_ack_time

    while True:
        try:
            if srPort is None or not srPort.is_open:
                time.sleep(1)
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


if srPort is not None:
    reader_thread = threading.Thread(target=read_from_esp, daemon=True)
    reader_thread.start()
    print("[UART] Đã khởi động thread đọc ESP32")


def transmit_data_to_mcu(main_green_time: int, cross_green_time: int):
    if srPort is None or not srPort.is_open:
        return False

    packet = f"M:{main_green_time}|C:{cross_green_time}\n"
    print(f"[UART TX] {packet.strip()}")

    try:
        with uart_lock:
            srPort.write(packet.encode("utf-8"))
            srPort.flush()
        return True
    except Exception as e:
        print(f"[UART] Lỗi gửi: {e}")
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
    counts_main = config["counts_main"]
    counts_cross = config["counts_cross"]

    q_main = calculate_pcu(counts_main)
    q_cross = calculate_pcu(counts_cross)
    t_main, t_cross = calculate_t_green(q_main, q_cross)

    print("=" * 55)
    print(f" NGÃ TƯ {cam_id} - {config['name']}")
    print(f" Main  → Car:{counts_main[0]} Bus:{counts_main[1]} Truck:{counts_main[2]} Motor:{counts_main[3]}")
    print(f" Cross → Car:{counts_cross[0]} Bus:{counts_cross[1]} Truck:{counts_cross[2]} Motor:{counts_cross[3]}")
    print(f" PCU: {q_main:.1f} / {q_cross:.1f}  |  Đèn xanh: {t_main:.0f}s / {t_cross:.0f}s")
    print("=" * 55)

    with uart_lock:
        current_mode = "adaptive" if is_adaptive else "fixed"

    update_control_local(cam_id, q_main, q_cross, t_main, t_cross, current_mode)
    # ===== CHỈ GỬI UART NẾU ĐÚNG CAMERA ĐANG ƯU TIÊN =====
    global current_uart_cam
    with active_lock:
        is_allowed = (cam_id == current_uart_cam)

    if current_mode == "adaptive" and srPort is not None:
        transmit_data_to_mcu(int(round(t_main)), int(round(t_cross)))
    else:
        if not is_allowed:
            print(f"[UART] Bỏ qua gửi từ cam {cam_id} (không phải camera đang ưu tiên)")
        else:
            print("[UART] Fixed-time hoặc không có Serial → không gửi")


def generate_frames(cam_id: str):
    config = INTERSECTIONS.get(cam_id)
    if not config:
        return

    # ============================================================
    # NẾU KHÔNG CÓ UART → TỪ CHỐI CHẠY MODEL + STREAM
    # ============================================================
    if srPort is None or not srPort.is_open:
        print(f"[BLOCK] Không có kết nối UART → từ chối khởi chạy model cam {cam_id}")
        # Cập nhật mode Fixed cho chắc
        update_control_local(cam_id, 0, 0, 30, 30, "fixed")
        return          # Generator rỗng → video feed bị tắt

    global current_uart_cam

    # Đánh dấu camera này đang active
    with active_lock:
        active_cameras.add(cam_id)
        current_uart_cam = cam_id          # Camera mới mở sẽ được ưu tiên
        print(f"[Active] Bắt đầu stream cam {cam_id} → ưu tiên UART: {current_uart_cam}")
    try:
        cap = cv2.VideoCapture(config["video"])
        if not cap.isOpened():
            print(f"[ERROR] Không mở được video: {config['video']}")
            return

        local_model = models[cam_id]
        track_history = {}
        counted_ids = set()
        frame_counter = 0
        FRAME_SKIP = 1
        last_print_time = time.time()
        PRINT_INTERVAL = 5.0

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
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

            # Vẽ đường đếm
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

                    # Vẽ box + label
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
                    cv2.circle(frame, curr_pt, 4, (0, 0, 255), -1)
                    label = f"{CLASS_NAMES[cls]} {obj_id} {conf:.2f}"
                    cv2.putText(frame, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                    if unique_id in track_history:
                        prev_pt = track_history[unique_id]

                        if unique_id not in counted_ids:
                            # Trục chính
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

                            # Trục phụ
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

            # Cập nhật PCU định kỳ
            if time.time() - last_print_time >= PRINT_INTERVAL:
                print_traffic_stats(cam_id, config)
                last_print_time = time.time()
            # Cap nhat thoi gian hoat dong cuoi cung
            with active_lock:
                camera_last_active[cam_id] = time.time()

            ret, buffer = cv2.imencode(".jpg", frame)
            if not ret:
                continue

            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")

    finally:
        # Khi client ngắt kết nối → xóa khỏi danh sách active
        with active_lock:
            active_cameras.discard(cam_id)
            if current_uart_cam == cam_id:
                # Nếu đây là camera đang ưu tiên → chuyển quyền cho camera khác (nếu còn)
                current_uart_cam = next(iter(active_cameras), None)
            print(f"[Active] Dừng stream cam {cam_id} → còn lại: {list(active_cameras)} | UART ưu tiên: {current_uart_cam}")
# Chạy standalone để test
if __name__ == "__main__":
    import sys
    cam_id = sys.argv[1] if len(sys.argv) > 1 else "1"
    print(f"[*] Test ngã tư {cam_id} (Ctrl+C để dừng)")
    try:
        for _ in generate_frames(cam_id):
            pass
    except KeyboardInterrupt:
        print("\n[*] Đã dừng")
        if cam_id in INTERSECTIONS:
            print_traffic_stats(cam_id, INTERSECTIONS[cam_id])
    finally:
        if srPort and srPort.is_open:
            srPort.close()
