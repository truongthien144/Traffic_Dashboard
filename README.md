# ITS.Core — Hệ thống điều khiển đèn giao thông thích nghi sử dụng phát hiện phương tiện dựa trên học sâu

Hệ thống điều khiển đèn giao thông thích nghi sử dụng phát hiện phương tiện dựa trên học sâu.

---

## 1. Tổng quan

| Thành phần | Vai trò |
|------------|---------|
| **Raspberry Pi 4** | YOLO phát hiện/đếm xe, tính PCU & thời gian đèn xanh, gửi UART xuống ESP32, phục vụ API + video stream |
| **ESP32-WROOM-32** | Nhận thời gian xanh, điều khiển LED + TM1637, DHT20, fallback Fixed-time khi mất gói tin |
| **Dashboard (React)** | Giám sát video AI, PCU, mode Adaptive/Fixed, phần cứng Pi & ESP32 |

**Luồng chính:**

Khi mất liên lạc UART / hết timeout → ESP và Dashboard chuyển **Fixed-time (30s / 30s)**.

---

## 2. Phần cứng

### Cụm điều khiển (ESP32)
- ESP32-WROOM-32  
- LED tín hiệu: Main (R/Y/G), Cross (R/Y/G)  
- 2 module 7 đoạn TM1637 (đếm ngược Main / Cross)  
- Cảm biến DHT20 (nhiệt độ, độ ẩm) — I2C (SDA 25, SCL 26)  
- USB-TTL (kết nối UART với Raspberry Pi)

### Nút biên
- Raspberry Pi (chạy YOLO + FastAPI)  
- Kết nối UART: Pi ↔ USB-TTL ↔ ESP32 (`/dev/ttyUSB0`, 115200 baud)

### Mạng
- Laptop / trình duyệt cùng LAN với Pi (hoặc Tailscale khi khác mạng)  
- Frontend gọi API theo IP của Pi (cổng `8000`)

---

## 3. Phần mềm

### Backend (Raspberry Pi)
- Python 3 + FastAPI + Uvicorn  
- Ultralytics YOLO (`best.pt`) + ByteTrack  
- OpenCV, pyserial, psutil  
- FreeRTOS-style logic phía ESP; trên Pi dùng thread worker cho từng camera  

### Frontend
- React + TypeScript + Vite  
- Tailwind CSS, Recharts, React Router  
- i18n (VI/EN) trên Landing  

### Firmware ESP32
- Arduino / PlatformIO  
- FreeRTOS tasks: UART, Traffic, DHT20  
- TM1637Display, DHT20  

---

## 4. Tính năng chính

- Phát hiện 4 lớp: Car, Bus, Truck, Motorcycle  
- Đếm khi quỹ đạo cắt **line ảo** Main / Cross  
- Quy đổi **PCU** và tính thời gian đèn xanh (15–45 s, chu kỳ tối đa 60 s)  
- Chế độ **Adaptive** khi còn UART + ACK; **Fixed-time** khi timeout / mất USB  
- Checksum XOR trên gói UART: `M:30|C:30*5A`  
- ESP gửi `ENV:T:xx|H:yy` định kỳ; Pi cập nhật Dashboard  
- Video MJPEG theo ngã tư, thống kê PCU, nhật ký sự kiện  
- Giám sát CPU/RAM/ổ đĩa/nhiệt độ Pi, trạng thái UART, uptime  

---

## 5. Giao thức UART (Pi ↔ ESP32)

**Pi → ESP32**

Ví dụ: `M:35|C:25*4B`

- Body: `M:35|C:25`  
- `*` + XOR 8-bit của toàn body, in hex 2 ký tự  
- ESP từ chối nếu thiếu `*`, sai checksum, hoặc `M,C < 15` / `M+C > 60`  

**ESP → Pi**

| Dòng | Ý nghĩa |
|------|---------|
| `[ACK] OK` | Nhận gói hợp lệ |
| `[FALLBACK] FIXED-TIME` | Hết timeout, về 30/30 |
| `ENV:T:28.5|H:65.0` | Nhiệt độ / độ ẩm DHT20 |
| `[CHECKSUM FAIL]...` / `[INVALID]` | Gói lỗi |

Timeout fallback phía ESP: **15 giây** không có gói hợp lệ.

---

## 6. Cấu trúc thư mục

- **backend** sẽ chứa các cấu hình lưu vị trí các video, file và hardcode đăng nhập. Đồng thời đây là nơi lưu trữ file trọng số YOLO26 và mã nguồn python suy luận, tính toán trên Raspberry.
- **traffic_dashboard** lưu trữ các mã nguồn giao diện (dashboard).
- **src** chứa firmware của ESP32.

## 7. Cài đặt & chạy

### 7.1. Raspberry Pi (backend)
Dùng dây tín hiệu kết nối Pi và laptop, sau đó mở Terminal:
```bash
ssh hostnamePi@IP_Pi
password: password_Pi
cd ~/Traffic_Dashboard   # thư mục chứa main.py
cd backend
python3 -m venv .venv-prod
source .venv-prod/bin/activate
pip install fastapi uvicorn ultralytics opencv-python-headless pyserial psutil pyjwt python-multipart (pip install -r requirements.txt)
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 7.2. Dashboard (frontend)
Mở PowerShell trên laptop Windows:
```bash
cd ~/Traffic_Dashboard/traffic_dashboard
venv\Scripts\activate
npm install
npm run dev
```

### 7.3. Nạp firmware vào ESP32:
- Mở Visual Studio Code, vào dự án của PlatformIO (Quick Access)
- Build
- Upload
