# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from config import INTERSECTIONS, ENVIRONMENT
from auth import LoginRequest, verify_login
from detect_edge import generate_frames, active_cameras, camera_last_active, active_lock, worker_running, srPort, UART_PORT, ensure_serial, uart_device_ok, uart_link_ok
from datetime import datetime, timedelta
import detect_edge
import psutil
import os
import time
app = FastAPI(title="ITS Core API - Edge Node")

# Biến toàn cục để tính lưu lượng mạng (delta)
_last_net = psutil.net_io_counters()
_last_net_time = time.time()

# Cho phép Frontend từ laptop
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Dev: cho tất cả.
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

    # Worker đang chạy VÀ còn UART
    worker_ok = worker_running.get(intersection_id, False)
    uart_ok = uart_link_ok()
    is_running = worker_ok and uart_ok
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
        "is_running": is_running,
        "uart_ok": uart_ok
    }

@app.get("/api/environment")
def get_environment():
    return ENVIRONMENT

@app.get("/api/system_stats")
def get_system_stats():
    global _last_net, _last_net_time

    # ===== CPU =====
    cpu_percent = psutil.cpu_percent(interval=0.3)

    # ===== RAM =====
    mem = psutil.virtual_memory()
    ram_used_gb = round(mem.used / (1024**3), 1)
    ram_total_gb = round(mem.total / (1024**3), 1)
    ram_percent = round(mem.percent, 1)

    # ===== Storage (microSD) =====
    disk = psutil.disk_usage('/')
    disk_percent = round(disk.percent, 1)

    # ===== CPU Temperature =====
    cpu_temp = None
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            cpu_temp = round(int(f.read().strip()) / 1000.0, 1)
    except Exception:
        cpu_temp = None

    # ===== Uptime (Thời gian hoạt động) =====
    boot_time = psutil.boot_time()
    uptime_seconds = int(time.time() - boot_time)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    # ===== Network (Lưu lượng dữ liệu) =====
    net = psutil.net_io_counters()
    now = time.time()
    time_delta = max(now - _last_net_time, 0.1)

    # Tính số packet / byte tăng thêm (có thể đổi sang bytes nếu muốn)
    tx_packets = net.packets_sent - _last_net.packets_sent
    rx_packets = net.packets_recv - _last_net.packets_recv

    # Cập nhật mốc
    _last_net = net
    _last_net_time = now
    # Thử mở lại UART nếu vừa cắm lại
    try:
     ensure_serial()
    except Exception:
     pass

    uart_ok = uart_link_ok()

    return {
        "cpu_percent": round(cpu_percent, 1),
        "ram_used_gb": ram_used_gb,
        "ram_total_gb": ram_total_gb,
        "ram_percent": ram_percent,
        "disk_percent": disk_percent,
        "cpu_temp": cpu_temp,
        "uptime": uptime_str,
        "uptime_seconds": uptime_seconds,
        "tx_packets": max(tx_packets, 0),
        "rx_packets": max(rx_packets, 0),
        "last_update": datetime.now().isoformat(),
        "uart_ok": uart_ok
    }

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
    intersections_info = []
    for cam_id, config in INTERSECTIONS.items():
        motos = config["counts_main"].get(3, 0) + config["counts_cross"].get(3, 0)
        cars = config["counts_main"].get(0, 0) + config["counts_cross"].get(0, 0)
        trucks = config["counts_main"].get(2, 0) + config["counts_cross"].get(2, 0)
        buses = config["counts_main"].get(1, 0) + config["counts_cross"].get(1, 0)
        pcu = (motos * 0.5) + (cars * 1) + (trucks * 2) + (buses * 2.5)
        total_pcu += pcu
        total_vehicles += (motos + cars + trucks + buses)

        intersections_info.append({
            "id": cam_id,
            "t_green_main": config.get("t_green_main", 30),
            "t_green_cross": config.get("t_green_cross", 30),
            "mode": config.get("mode", "fixed"),
        })
    # Chỉ coi là active nếu còn gửi frame trong 8 giây gần nhất
    now = time.time()
    truly_active = []
    with active_lock:
        for cam_id in list(active_cameras):
            last = camera_last_active.get(cam_id, 0)
            if now - last <= 8:
                truly_active.append(cam_id)
            else:
                # Tự dọn camera “zombie”
                active_cameras.discard(cam_id)
                camera_last_active.pop(cam_id, None)
    return {
        "total_intersections": len(INTERSECTIONS),
        "active_nodes": len(truly_active),
        "active_cameras": truly_active,
        "total_pcu": round(total_pcu),
        "total_vehicles_24h": total_vehicles,
        "system_status": "Ổn định" if True else "Mất kết nối",
        "intersections": intersections_info,
    }
