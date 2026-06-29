# Notification Service (A7) — Dịch vụ gửi cảnh báo đa kênh

Service của nhóm **A7** trong Demo Day Smart Campus (FIT4110).
Nhận cảnh báo từ **Core Business (A6)** qua REST, rồi gửi ra **đa kênh** (Telegram / Email / Log) theo mức độ `severity`.

> Contract đã chốt với A6: xem `../Contract_A6-A7_CONFIRMED_v1.md`.

---

## 1. Kiến trúc tổng quan

```text
A6 (Core)  --REST POST /api/v1/alerts-->  A7 (Notification)
                                              -> định tuyến theo severity
                                              -> gửi: Telegram / Email / Log
                                              -> trả 202 Accepted
```

- **Framework:** FastAPI (Python 3.11)
- **Cổng:** 8000 (bind `0.0.0.0`, publish ra host)
- **A6 là bên gọi (consumer), A7 là bên nhận (provider).**

---

## 2. Yêu cầu máy (chuẩn bị trước)

| Cần | Ghi chú |
|---|---|
| **Docker Desktop** | Bắt buộc. Tải tại https://www.docker.com/. Mở Docker Desktop và đợi nó "Running" trước khi chạy. |
| **Internet** | Để build image và để kênh Telegram gửi được. |
| (tùy chọn) **Python 3.10+** | Chỉ cần nếu muốn chạy `tools/` hoặc `pytest` ngoài Docker. |

Kiểm tra Docker đã sẵn sàng:
```bash
docker version
docker compose version
```

---

## 3. Chạy nhanh trên máy MỚI (4 bước)

### Bước 1 — Copy/clone toàn bộ thư mục `demo-day-team-notify` sang máy mới.

### Bước 2 — Tạo file cấu hình `.env`
File `.env` **không có sẵn** (đã bị gitignore vì chứa token). Tạo từ mẫu:

```bash
# Windows PowerShell
copy .env.example .env
# macOS / Linux / Git Bash
cp .env.example .env
```

Mở `.env` và điền **Telegram** (xem cách lấy ở mục 5). Tối thiểu 2 dòng:
```env
TELEGRAM_BOT_TOKEN=<token-bot-cua-ban>
TELEGRAM_CHAT_ID=<chat-id-cua-ban>
```
> Nếu để trống Telegram/Email, service vẫn chạy được — chỉ gửi ra kênh `log` (xem trong `docker compose logs`). Đủ để demo luồng, nhưng không có tin nhắn thật.

### Bước 3 — Build và chạy
```bash
docker compose up -d --build
```

### Bước 4 — Kiểm tra service sống
```bash
curl http://127.0.0.1:8000/health
```
Mong đợi:
```json
{ "status": "ok", "service": "notification", "version": "1.0.0" }
```

Xong! Service đang chạy nền. Xem log realtime:
```bash
docker compose logs -f
```

Dừng service:
```bash
docker compose down
```

---

## 4. Tự test khi A6 chưa sẵn sàng (mock Core)

Không cần chờ nhóm Core. Tự bắn alert thử bằng script mock (chỉ dùng Python chuẩn):

```bash
python tools/mock_core_send.py                                   # alert high mặc định
python tools/mock_core_send.py --severity medium --title "Khoi" --message "Phong B201 co khoi"
python tools/mock_core_send.py --severity high   --channels log,telegram
python tools/mock_core_send.py --url http://<RADMIN_IP_A7>:8000/api/v1/alerts   # test qua mạng
```

Hoặc dùng `curl` trực tiếp:
```bash
curl -X POST http://localhost:8000/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","message":"Chay lab A101","severity":"high"}'
```

Mong đợi trả `202 Accepted`. Mở `docker compose logs` thấy dòng `[NOTIFY:telegram] đã gửi` là Telegram đã bắn thật.

---

## 5. Cấu hình Telegram (kênh chính, dễ demo nhất)

1. Mở Telegram → tìm **@BotFather** → gửi `/newbot` → đặt tên + username (kết thúc bằng `bot`) → **copy TOKEN**.
2. Tìm **đúng bot vừa tạo** (theo username), mở chat với nó, bấm **START** (hoặc gửi `hi`). Bước này bắt buộc.
3. Lấy `chat_id` tự động:
   ```bash
   python tools/telegram_setup.py --token <TOKEN>
   ```
4. Điền `TELEGRAM_BOT_TOKEN` và `TELEGRAM_CHAT_ID` vào `.env`.
5. Gửi thử:
   ```bash
   python tools/telegram_setup.py --token <TOKEN> --chat-id <CHAT_ID> --send
   ```
6. `docker compose up -d --force-recreate` để service nạp `.env` mới.

> Lưu ý: đổi máy/đổi bot thì phải lấy lại `chat_id` và cập nhật `.env`.

### (Tùy chọn) Email/SMTP — kênh phụ
Email dễ bị chặn port ở mạng trường, chỉ nên làm phụ. Dùng port **587 (STARTTLS)**, Gmail cần **App Password**:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=ban@gmail.com
SMTP_PASSWORD=<App Password 16 ky tu>
EMAIL_FROM=ban@gmail.com
EMAIL_TO=nguoinhan@gmail.com
```

---

## 6. API (tóm tắt theo contract)

### `GET /health`
```json
{ "status": "ok", "service": "notification", "version": "1.0.0" }
```

### `POST /api/v1/alerts`
Request (bắt buộc: `title`, `message`, `severity`):
```json
{
  "title": "Canh bao nhiet do",
  "message": "Lab A101: nhiet do 42C - nguy hiem",
  "severity": "high",
  "source_service": "team-core",
  "event_id": "core-sensor-event-001",
  "timestamp": "2026-06-18T14:30:11+07:00",
  "location": "Lab A101"
}
```
Response `202`:
```json
{ "status":"accepted", "notification_id":"notif-xxxxxxxx",
  "received_event_id":"core-sensor-event-001", "channels":["telegram","email","log"] }
```
- Thiếu/sai field → `422` `{ "status":"error","error":"validation_error","missing_fields":[...] }`
- Trùng `event_id` → `200` `{ "status":"duplicate", ... }`
- Lỗi nội bộ → `500` `{ "status":"error","error":"internal_error","message":"..." }`

**Định tuyến kênh mặc định** (khi không truyền `channels`):
```text
high   -> telegram + email + log
medium -> email + log
low    -> log
```

---

## 7. Tích hợp với A6 trong Demo Day (qua Radmin VPN)

1. Cài **Radmin VPN** (https://www.radmin-vpn.com/), join network **`DVKN-CNTT17-07_A`**.
2. Lấy **Radmin IP** của máy (dạng `26.x.x.x`) → **báo cho A6** (A6 ở `26.13.125.86`).
3. Mở **firewall TCP 8000** (PowerShell Admin trên Windows):
   ```powershell
   netsh advfirewall firewall add rule name="FIT4110 Demo API 8000" dir=in action=allow protocol=TCP localport=8000
   ```
4. `docker compose up -d --build` (service bind `0.0.0.0:8000`).
5. Nhờ A6 ping `http://<RADMIN_IP_A7>:8000/health`, rồi gửi alert thật `POST /api/v1/alerts`.
6. Chụp minh chứng (tin nhắn Telegram + log) lưu vào `reports/`.

---

## 8. Unit test
```bash
pip install -r requirements.txt
pytest -q
```
Bộ test phủ: health, định tuyến theo severity, lỗi validate 422, chống trùng event_id.

---

## 9. Cấu trúc dự án
```text
demo-day-team-notify/
├── README.md                  # file này
├── Dockerfile                 # build image (multi-stage, non-root, healthcheck)
├── docker-compose.yml         # 1 service "api", port 8000
├── requirements.txt
├── .env.example               # mẫu cấu hình (copy thành .env)
├── .gitignore                 # .env bị loại trừ (không commit token)
├── src/notify_app/
│   ├── main.py                # FastAPI: /health, POST /api/v1/alerts
│   ├── models.py              # schema AlertRequest / response
│   └── channels.py            # gửi đa kênh + định tuyến theo severity
├── tests/test_notify.py       # unit test
└── tools/
    ├── mock_core_send.py      # giả lập A6 gửi alert (test độc lập)
    └── telegram_setup.py      # lấy chat_id + gửi tin thử
```

---

## 10. Xử lý sự cố

| Triệu chứng | Nguyên nhân & cách xử lý |
|---|---|
| `curl /health` không phản hồi / connection refused | Container chưa chạy → `docker compose ps`; Docker Desktop chưa mở; hoặc cổng 8000 bị service khác chiếm. |
| `port is already allocated` khi `up` | Cổng 8000 đang bị app khác dùng (vd service A1) → tắt app đó, hoặc đổi `APP_PORT` trong `.env`. |
| Trả 202 nhưng không có tin Telegram | `.env` thiếu/sai `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID`; hoặc chưa `--force-recreate` sau khi sửa `.env`. Xem log `[NOTIFY:telegram] ...`. |
| `telegram_setup.py` báo "Chua thay tin nhan" | Chưa bấm START / chưa nhắn cho **đúng bot** trên Telegram. |
| Máy A6 gọi bị timeout | Chưa mở firewall 8000; chưa join đúng Radmin network; hoặc dùng sai IP (phải là Radmin IP `26.x.x.x`). |
| Sửa `.env` mà không có tác dụng | Phải `docker compose up -d --force-recreate` để nạp lại biến môi trường. |
