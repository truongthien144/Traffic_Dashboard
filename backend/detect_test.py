import cv2
import time
from datetime import datetime
from ultralytics import YOLO
from config import INTERSECTIONS

print("[*] Đang khởi tạo bộ nhớ độc lập cho 3 ngã tư...")

# ============================================================
# TẠO 3 MÔ HÌNH ĐỘC LẬP
# ============================================================
models = {
    "1": YOLO('best.pt'),
    "2": YOLO('best.pt'),
    "3": YOLO('best.pt')
}

CLASS_NAMES = {
    0: 'Car',
    1: 'Bus',
    2: 'Truck',
    3: 'Motorcycle'
}


# ============================================================
# CẤU HÌNH TÍNH THỜI GIAN ĐÈN
# ============================================================
C_MAX = 60          # Chu kỳ tối đa
T_GREEN_MIN = 15    # Thời gian xanh tối thiểu
T_GREEN_MAX = 45    # Thời gian xanh tối đa


# ============================================================
# KIỂM TRA GIAO CẮT
# ============================================================
def ccw(A, B, C):
    return (
        (C[1] - A[1]) * (B[0] - A[0])
        > (B[1] - A[1]) * (C[0] - A[0])
    )


def intersect(A, B, C, D):
    return (
        ccw(A, C, D) != ccw(B, C, D)
        and
        ccw(A, B, C) != ccw(A, B, D)
    )


# ============================================================
# TÍNH PCU CHO MỘT TRỤC
# ============================================================
def calculate_pcu(counts):
    """
    Tính PCU từ số lượng phương tiện của một trục.

    Motorcycle = 0.5
    Car        = 1
    Truck      = 2
    Bus        = 2
    """

    motos = counts.get(3, 0)
    cars = counts.get(0, 0)
    trucks = counts.get(2, 0)
    buses = counts.get(1, 0)

    pcu = (
        (motos * 0.5)
        + (cars * 1)
        + (trucks * 2)
        + (buses * 2)
    )

    return pcu


# ============================================================
# TÍNH TGREEN CHO HAI TRỤC
# ============================================================
def calculate_tgreen(pcu_main, pcu_cross):
    """
    Tính thời gian đèn xanh cho Trục chính và Trục phụ.

    Tgreen_main  = PCU_main / Total_PCU * C_MAX
    Tgreen_cross = C_MAX - Tgreen_main

    Giới hạn mỗi Tgreen trong khoảng 15-45 giây.
    """

    total_pcu = pcu_main + pcu_cross

    # Không có phương tiện
    if total_pcu == 0:
        return 30, 30

    # Tính thời gian xanh Trục chính
    tgreen_main = (
        pcu_main / total_pcu
    ) * C_MAX

    # Làm tròn về số nguyên
    tgreen_main = int(round(tgreen_main))

    # Giới hạn 15-45 giây
    tgreen_main = max(
        T_GREEN_MIN,
        min(T_GREEN_MAX, tgreen_main)
    )

    # Trục phụ nhận phần thời gian còn lại
    tgreen_cross = C_MAX - tgreen_main

    # Bảo vệ giới hạn
    tgreen_cross = max(
        T_GREEN_MIN,
        min(T_GREEN_MAX, tgreen_cross)
    )

    return tgreen_main, tgreen_cross


# ============================================================
# IN KẾT QUẢ RA TERMINAL
# ============================================================
def print_traffic_result(config):
    """
    In số lượng xe, PCU và Tgreen của từng trục.
    """

    counts_main = config["counts_main"]
    counts_cross = config["counts_cross"]

    # --------------------------------------------------------
    # PCU từng trục
    # --------------------------------------------------------
    pcu_main = calculate_pcu(counts_main)
    pcu_cross = calculate_pcu(counts_cross)

    total_pcu = pcu_main + pcu_cross

    # --------------------------------------------------------
    # TGREEN
    # --------------------------------------------------------
    tgreen_main, tgreen_cross = calculate_tgreen(
        pcu_main,
        pcu_cross
    )

    # --------------------------------------------------------
    # Tổng số phương tiện
    # --------------------------------------------------------
    total_main = sum(counts_main.values())
    total_cross = sum(counts_cross.values())
    total_vehicles = total_main + total_cross

    # ========================================================
    # TERMINAL OUTPUT
    # ========================================================
    print("\n")
    print("=" * 60)
    print(f"NGÃ TƯ: {config['name']}")
    print("=" * 60)

    print("\n[TRỤC CHÍNH]")
    print(
        f"  Car        : {counts_main.get(0, 0)}"
    )
    print(
        f"  Bus        : {counts_main.get(1, 0)}"
    )
    print(
        f"  Truck      : {counts_main.get(2, 0)}"
    )
    print(
        f"  Motorcycle : {counts_main.get(3, 0)}"
    )

    print(f"  Tổng xe    : {total_main}")
    print(f"  PCU        : {pcu_main:.1f}")
    print(f"  Tgreen     : {tgreen_main} s")

    print("\n[TRỤC PHỤ]")
    print(
        f"  Car        : {counts_cross.get(0, 0)}"
    )
    print(
        f"  Bus        : {counts_cross.get(1, 0)}"
    )
    print(
        f"  Truck      : {counts_cross.get(2, 0)}"
    )
    print(
        f"  Motorcycle : {counts_cross.get(3, 0)}"
    )

    print(f"  Tổng xe    : {total_cross}")
    print(f"  PCU        : {pcu_cross:.1f}")
    print(f"  Tgreen     : {tgreen_cross} s")

    print("\n[TỔNG]")
    print(f"  Tổng xe    : {total_vehicles}")
    print(f"  Tổng PCU   : {total_pcu:.1f}")

    print("\n[TIME ALLOCATION]")
    print(f"  Main Green : {tgreen_main} s")
    print(f"  Cross Green: {tgreen_cross} s")

    print("=" * 60)


# ============================================================
# XỬ LÝ VIDEO
# ============================================================
def generate_frames(cam_id: str):

    config = INTERSECTIONS.get(cam_id)

    if not config:
        print(f"[ERROR] Không tìm thấy cấu hình cam_id = {cam_id}")
        return

    print(f"\n[*] Đang mở video: {config['video']}")

    cap = cv2.VideoCapture(config["video"])

    if not cap.isOpened():
        print(
            f"[ERROR] Không thể mở video: "
            f"{config['video']}"
        )
        return

    # Lấy đúng mô hình của ngã tư này
    local_model = models[cam_id]

    track_history = {}
    counted_ids = set()

    frame_counter = 0
    FRAME_SKIP = 1

    # ========================================================
    # CHẠY VIDEO
    # ========================================================
    while cap.isOpened():

        success, frame = cap.read()

        # ----------------------------------------------------
        # Video kết thúc → quay lại frame đầu
        # ----------------------------------------------------
        if not success:

            print("\n[*] Video kết thúc.")
            print("[*] Kết quả hiện tại:")

            print_traffic_result(config)

            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

            track_history.clear()
            counted_ids.clear()

            continue

        frame_counter += 1

        if frame_counter % FRAME_SKIP != 0:
            continue

        # ====================================================
        # YOLO TRACKING
        # ====================================================
        results = local_model.track(
            frame,
            persist=True,
            conf=0.25,
            imgsz=640,
            tracker="bytetrack.yaml",
            verbose=False
        )

        # ====================================================
        # VẼ LINE TRỤC CHÍNH
        # ====================================================
        for line in config["main_lines"]:
            cv2.line(
                frame,
                line[0],
                line[1],
                (0, 255, 0),
                2
            )

        # ====================================================
        # VẼ LINE TRỤC PHỤ
        # ====================================================
        for line in config["cross_lines"]:
            cv2.line(
                frame,
                line[0],
                line[1],
                (255, 0, 0),
                2
            )

        # ====================================================
        # XỬ LÝ OBJECT
        # ====================================================
        if results[0].boxes.id is not None:

            boxes = (
                results[0]
                .boxes
                .xyxy
                .cpu()
                .numpy()
            )

            clss = (
                results[0]
                .boxes
                .cls
                .cpu()
                .numpy()
            )

            ids = (
                results[0]
                .boxes
                .id
                .cpu()
                .numpy()
            )

            confs = (
                results[0]
                .boxes
                .conf
                .cpu()
                .numpy()
            )

            # ------------------------------------------------
            # Duyệt từng phương tiện
            # ------------------------------------------------
            for box, cls, obj_id, conf in zip(
                boxes,
                clss,
                ids,
                confs
            ):

                x1, y1, x2, y2 = box

                cls = int(cls)
                obj_id = int(obj_id)

                unique_id = f"{cam_id}_{obj_id}"

                if cls not in CLASS_NAMES:
                    continue

                # --------------------------------------------
                # Tâm bounding box
                # --------------------------------------------
                xc = int((x1 + x2) / 2)
                yc = int((y1 + y2) / 2)

                curr_pt = (xc, yc)

                # --------------------------------------------
                # Bounding box
                # --------------------------------------------
                cv2.rectangle(
                    frame,
                    (int(x1), int(y1)),
                    (int(x2), int(y2)),
                    (255, 255, 0),
                    2
                )

                # --------------------------------------------
                # Center point
                # --------------------------------------------
                cv2.circle(
                    frame,
                    curr_pt,
                    4,
                    (0, 0, 255),
                    -1
                )

                # --------------------------------------------
                # Label
                # --------------------------------------------
                label = (
                    f"{CLASS_NAMES[cls]} "
                    f"{obj_id} "
                    f"{conf:.2f}"
                )

                cv2.putText(
                    frame,
                    label,
                    (int(x1), int(y1) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 0),
                    2
                )

                # =================================================
                # KIỂM TRA QUỸ ĐẠO
                # =================================================
                if unique_id in track_history:

                    prev_pt = track_history[unique_id]

                    # ---------------------------------------------
                    # Chỉ đếm mỗi ID một lần
                    # ---------------------------------------------
                    if unique_id not in counted_ids:

                        # =========================================
                        # TRỤC CHÍNH
                        # =========================================
                        for line in config["main_lines"]:

                            if intersect(
                                prev_pt,
                                curr_pt,
                                line[0],
                                line[1]
                            ):

                                config["counts_main"][cls] += 1

                                counted_ids.add(unique_id)

                                cv2.line(
                                    frame,
                                    line[0],
                                    line[1],
                                    (0, 0, 255),
                                    6
                                )

                                # ---------------------------------
                                # Ghi event
                                # ---------------------------------
                                now = datetime.now().strftime(
                                    "%H:%M:%S"
                                )

                                event = {
                                    "id": (
                                        int(time.time() * 1000)
                                        + obj_id
                                    ),
                                    "time": now,
                                    "message": (
                                        f"Phát hiện "
                                        f"{CLASS_NAMES[cls]} "
                                        f"qua Trục Chính"
                                    ),
                                    "type": "vehicle",
                                    "vehicle_type": (
                                        CLASS_NAMES[cls]
                                    ),
                                    "conf": f"{conf:.2f}"
                                }

                                config["events"].insert(
                                    0,
                                    event
                                )

                                print(
                                    f"[COUNT MAIN] "
                                    f"{CLASS_NAMES[cls]} "
                                    f"ID={obj_id}"
                                )

                                break

                        # =========================================
                        # TRỤC PHỤ
                        # =========================================
                        for line in config["cross_lines"]:

                            if intersect(
                                prev_pt,
                                curr_pt,
                                line[0],
                                line[1]
                            ):

                                config["counts_cross"][cls] += 1

                                counted_ids.add(unique_id)

                                cv2.line(
                                    frame,
                                    line[0],
                                    line[1],
                                    (0, 0, 255),
                                    6
                                )

                                # ---------------------------------
                                # Ghi event
                                # ---------------------------------
                                now = datetime.now().strftime(
                                    "%H:%M:%S"
                                )

                                event = {
                                    "id": (
                                        int(time.time() * 1000)
                                        + obj_id
                                    ),
                                    "time": now,
                                    "message": (
                                        f"Phát hiện "
                                        f"{CLASS_NAMES[cls]} "
                                        f"qua Trục Phụ"
                                    ),
                                    "type": "vehicle",
                                    "vehicle_type": (
                                        CLASS_NAMES[cls]
                                    ),
                                    "conf": f"{conf:.2f}"
                                }

                                config["events"].insert(
                                    0,
                                    event
                                )

                                print(
                                    f"[COUNT CROSS] "
                                    f"{CLASS_NAMES[cls]} "
                                    f"ID={obj_id}"
                                )

                                break

                        # -----------------------------------------
                        # Giới hạn 15 event gần nhất
                        # -----------------------------------------
                        if len(config["events"]) > 15:
                            config["events"].pop()

                # ---------------------------------------------
                # Lưu vị trí hiện tại
                # ---------------------------------------------
                track_history[unique_id] = curr_pt

        # ====================================================
        # HIỂN THỊ FRAME
        # ====================================================
        ret, buffer = cv2.imencode(
            '.jpg',
            frame
        )

        frame_bytes = buffer.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n'
            + frame_bytes
            + b'\r\n'
        )
