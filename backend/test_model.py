"""
Kiểm tra chi tiết file best.pt để viết báo cáo
"""
from ultralytics import YOLO
import torch
from pathlib import Path

WEIGHT = "best.pt"  # đổi đường dẫn nếu cần

def main():
    path = Path(WEIGHT)
    print("=" * 60)
    print(" BÁO CÁO KIỂM TRA MÔ HÌNH YOLO")
    print("=" * 60)

    # ----- 1. Thông tin file -----
    size_mb = path.stat().st_size / (1024 * 1024)
    print("\n[1] THÔNG TIN FILE")
    print(f"  Đường dẫn     : {path.resolve()}")
    print(f"  Kích thước    : {size_mb:.2f} MB")

    # ----- 2. Load model -----
    model = YOLO(str(path))
    ckpt = getattr(model, "ckpt", None) or {}

    print("\n[2] LOẠI MÔ HÌNH & BÀI TOÁN")
    print(f"  Task          : {model.task}")
    print(f"  Kiến trúc     : YOLO26n (nano)")
    print(f"  Model yaml    : {ckpt.get('train_args', {}).get('model', 'N/A')}")
    print(f"  Type          : {type(model.model).__name__}")

    # ----- 3. Class -----
    print("\n[3] LỚP ĐỐI TƯỢNG (CLASSES)")
    print(f"  Số lượng class: {len(model.names)}")
    for i, name in model.names.items():
        print(f"    {i}: {name}")

    # ----- 4. Kiến trúc / độ phức tạp -----
    print("\n[4] ĐỘ PHỨC TẠP MÔ HÌNH")
    # model.info() in ra summary; lấy thêm số tham số
    n_params = sum(p.numel() for p in model.model.parameters())
    n_trainable = sum(p.numel() for p in model.model.parameters() if p.requires_grad)
    print(f"  Tổng parameters   : {n_params:,}")
    print(f"  Trainable params  : {n_trainable:,}")
    print(f"  (Tham khảo) YOLO26n ~ 2.5M params, ~5.9 GFLOPs @ 640")

    # In summary chuẩn Ultralytics
    print("\n  --- Ultralytics model.info() ---")
    model.info(detailed=False)

    # ----- 5. Tham số lúc train -----
    print("\n[5] THAM SỐ HUẤN LUYỆN (nếu còn trong checkpoint)")
    args = ckpt.get("train_args") or ckpt.get("args") or {}
    if args:
        keys = [
            "model", "data", "epochs", "imgsz", "batch", "lr0", "lrf",
            "optimizer", "device", "workers", "patience", "pretrained",
            "optimizer", "momentum", "weight_decay", "seed"
        ]
        for k in keys:
            if k in args:
                print(f"  {k:15}: {args[k]}")
        # in thêm vài key khác nếu có
        for k, v in args.items():
            if k not in keys and k in ("box", "cls", "dfl", "hsv_h", "hsv_s", "hsv_v", "degrees", "translate", "scale", "fliplr"):
                print(f"  {k:15}: {v}")
    else:
        print("  Không tìm thấy train_args trong checkpoint.")

    print(f"\n  Epoch (ckpt)     : {ckpt.get('epoch', 'N/A')}")
    print(f"  Best fitness     : {ckpt.get('best_fitness', 'N/A')}")

    # ----- 6. Metric nếu còn lưu -----
    print("\n[6] METRIC (nếu có trong checkpoint)")
    for key in ("best_fitness", "fitness", "metrics", "ema"):
        if key in ckpt and ckpt[key] is not None:
            val = ckpt[key]
            if key == "metrics" and isinstance(val, dict):
                for mk, mv in val.items():
                    print(f"  {mk}: {mv}")
            else:
                print(f"  {key}: {val}")

    # ----- 7. Gợi ý đoạn viết báo cáo -----
    print("\n" + "=" * 60)
    print(" GỢI Ý ĐOẠN MÔ TẢ CHO BÁO CÁO")
    print("=" * 60)
    print(f"""
Mô hình phát hiện phương tiện sử dụng kiến trúc YOLO26n (phiên bản nano),
thuộc bài toán object detection. Mô hình được huấn luyện nhận diện 4 lớp
đối tượng: Car, Bus, Truck, Motorcycle. Kích thước đầu vào (imgsz) là 640,
số epoch huấn luyện là {args.get('epochs', 60)}.

YOLO26n có khoảng 2,5 triệu tham số và ~5,9 GFLOPs, phù hợp triển khai
trên thiết bị biên (Raspberry Pi) nhờ dung lượng nhẹ (~{size_mb:.1f} MB)
và tốc độ suy luận nhanh so với các biến thể lớn hơn (s/m/l/x).
""")

if __name__ == "__main__":
    main()
