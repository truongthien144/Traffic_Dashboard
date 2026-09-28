#!/usr/bin/env python3
"""
test_uart_cluster.py
Test cụm kết nối Raspberry Pi ↔ ESP32 (UART)
+ In thông số hiệu năng/tiêu hao (psutil) giống /api/system_stats
Không dùng YOLO, không cần FastAPI.
"""

import serial
import time
import os
import threading
from datetime import datetime

try:
    import psutil
except ImportError:
    print("Cần cài: pip install psutil pyserial")
    raise

# ==================== CẤU HÌNH ====================
UART_PORT = "/dev/ttyUSB0"   # Đổi nếu cần: /dev/serial0, /dev/ttyAMA0
BAUD = 115200
SEND_INTERVAL = 5.0          # giây gửi 1 gói M:C
STATS_INTERVAL = 3.0         # giây in 1 lần thống kê hệ thống
TEST_M, TEST_C = 30, 30      # giá trị test (phải >= 15, tổng <= 60)

# ==================== TRẠNG THÁI ====================
srPort = None
lock = threading.Lock()

stats = {
    "tx_ok": 0,
    "tx_fail": 0,
    "rx_ack": 0,
    "rx_fallback": 0,
    "rx_env": 0,
    "rx_other": 0,
    "checksum_fail_seen": 0,
    "last_ack_rtt_ms": None,
    "last_env_temp": None,
    "last_env_humi": None,
    "last_esp_line": None,
    "pending_tx_time": None,
}

_last_net = None
_last_net_time = None


def xor_checksum(body: str) -> str:
    cs = 0
    for ch in body:
        cs ^= ord(ch)
    return f"{cs:02X}"


def build_packet(m: int, c: int) -> str:
    body = f"M:{m}|C:{c}"
    return f"{body}*{xor_checksum(body)}\n"


def get_pi_stats():
    global _last_net, _last_net_time

    cpu = psutil.cpu_percent(interval=0.2)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    cpu_temp = None
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            cpu_temp = round(int(f.read().strip()) / 1000.0, 1)
    except Exception:
        pass

    uptime_s = int(time.time() - psutil.boot_time())
    h, rem = divmod(uptime_s, 3600)
    m, s = divmod(rem, 60)
    uptime_str = f"{h:02d}:{m:02d}:{s:02d}"

    net = psutil.net_io_counters()
    now = time.time()
    if _last_net is None:
        tx_p = rx_p = 0
    else:
        dt = max(now - _last_net_time, 0.1)
        tx_p = max(net.packets_sent - _last_net.packets_sent, 0)
        rx_p = max(net.packets_recv - _last_net.packets_recv, 0)
    _last_net = net
    _last_net_time = now

    return {
        "cpu_percent": round(cpu, 1),
        "ram_used_gb": round(mem.used / (1024**3), 1),
        "ram_total_gb": round(mem.total / (1024**3), 1),
        "ram_percent": round(mem.percent, 1),
        "disk_percent": round(disk.percent, 1),
        "cpu_temp": cpu_temp,
        "uptime": uptime_str,
        "tx_packets": tx_p,
        "rx_packets": rx_p,
    }


def open_serial():
    global srPort
    if not os.path.exists(UART_PORT):
        print(f"[ERR] Không thấy cổng {UART_PORT}")
        return False
    try:
        if srPort and srPort.is_open:
            srPort.close()
    except Exception:
        pass
    try:
        srPort = serial.Serial(UART_PORT, BAUD, timeout=0.2)
        time.sleep(1.5)
        srPort.reset_input_buffer()
        print(f"[OK] Đã mở {UART_PORT} @ {BAUD}")
        return True
    except Exception as e:
        print(f"[ERR] Mở UART thất bại: {e}")
        srPort = None
        return False


def reader_loop(stop_event: threading.Event):
    while not stop_event.is_set():
        try:
            if srPort is None or not srPort.is_open:
                time.sleep(0.5)
                continue
            if srPort.in_waiting <= 0:
                time.sleep(0.02)
                continue

            line = srPort.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                continue

            ts = datetime.now().strftime("%H:%M:%S")
            with lock:
                stats["last_esp_line"] = line

            if line.startswith("[ACK]"):
                with lock:
                    stats["rx_ack"] += 1
                    if stats["pending_tx_time"] is not None:
                        rtt = (time.time() - stats["pending_tx_time"]) * 1000
                        stats["last_ack_rtt_ms"] = round(rtt, 1)
                        stats["pending_tx_time"] = None
                print(f"[{ts}] [ESP] {line}  | RTT≈{stats['last_ack_rtt_ms']} ms")

            elif line.startswith("[FALLBACK]"):
                with lock:
                    stats["rx_fallback"] += 1
                print(f"[{ts}] [ESP] {line}")

            elif line.startswith("ENV:"):
                with lock:
                    stats["rx_env"] += 1
                try:
                    parts = line[4:].split("|")
                    temp = float(parts[0].split(":")[1])
                    humi = float(parts[1].split(":")[1])
                    with lock:
                        stats["last_env_temp"] = temp
                        stats["last_env_humi"] = humi
                    print(f"[{ts}] [ENV] T={temp}°C  H={humi}%")
                except Exception:
                    print(f"[{ts}] [ENV] parse lỗi: {line}")

            elif "CHECKSUM FAIL" in line:
                with lock:
                    stats["checksum_fail_seen"] += 1
                print(f"[{ts}] [ESP] {line}")

            else:
                with lock:
                    stats["rx_other"] += 1
                print(f"[{ts}] [ESP] {line}")

        except Exception as e:
            print(f"[UART READ] {e}")
            time.sleep(0.3)


def send_test_packet():
    if srPort is None or not srPort.is_open:
        return False
    packet = build_packet(TEST_M, TEST_C)
    try:
        with lock:
            stats["pending_tx_time"] = time.time()
        srPort.write(packet.encode("utf-8"))
        srPort.flush()
        with lock:
            stats["tx_ok"] += 1
        print(f"[TX] {packet.strip()}")
        return True
    except Exception as e:
        with lock:
            stats["tx_fail"] += 1
            stats["pending_tx_time"] = None
        print(f"[TX FAIL] {e}")
        return False


def print_report():
    pi = get_pi_stats()
    with lock:
        s = dict(stats)

    total_tx = s["tx_ok"] + s["tx_fail"]
    ack_rate = (s["rx_ack"] / s["tx_ok"] * 100) if s["tx_ok"] else 0.0

    print("\n" + "=" * 60)
    print(f"  BÁO CÁO CỤM UART  |  {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    print("  [UART]")
    print(f"    Cổng           : {UART_PORT}  open={srPort is not None and getattr(srPort, 'is_open', False)}")
    print(f"    TX OK / FAIL   : {s['tx_ok']} / {s['tx_fail']}  (tổng {total_tx})")
    print(f"    RX ACK         : {s['rx_ack']}   (tỷ lệ ACK/TX ≈ {ack_rate:.0f}%)")
    print(f"    RX FALLBACK    : {s['rx_fallback']}")
    print(f"    RX ENV         : {s['rx_env']}")
    print(f"    RTT ACK gần nhất: {s['last_ack_rtt_ms']} ms")
    print(f"    ENV gần nhất   : T={s['last_env_temp']}°C  H={s['last_env_humi']}%")
    print("-" * 60)
    print("  [PI - psutil]")
    print(f"    CPU            : {pi['cpu_percent']}%")
    print(f"    RAM            : {pi['ram_used_gb']}/{pi['ram_total_gb']} GB  ({pi['ram_percent']}%)")
    print(f"    Disk           : {pi['disk_percent']}%")
    print(f"    CPU temp       : {pi['cpu_temp']} °C")
    print(f"    Uptime         : {pi['uptime']}")
    print(f"    Net packets    : Tx {pi['tx_packets']} / Rx {pi['rx_packets']} (delta lần in)")
    print("=" * 60 + "\n")


def main():
    print("[*] Test cụm ESP32 ↔ Raspberry Pi (UART)")
    print("[*] Ctrl+C để dừng\n")

    if not open_serial():
        return

    stop = threading.Event()
    t = threading.Thread(target=reader_loop, args=(stop,), daemon=True)
    t.start()

    last_send = 0.0
    last_stats = 0.0

    try:
        while True:
            now = time.time()

            if now - last_send >= SEND_INTERVAL:
                if not (srPort and srPort.is_open and os.path.exists(UART_PORT)):
                    print("[WARN] Mất cổng UART, thử mở lại...")
                    open_serial()
                else:
                    send_test_packet()
                last_send = now

            if now - last_stats >= STATS_INTERVAL:
                print_report()
                last_stats = now

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n[*] Dừng test")
    finally:
        stop.set()
        print_report()
        try:
            if srPort and srPort.is_open:
                srPort.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
