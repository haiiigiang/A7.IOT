# A7 — Notification Service · Giải thích cho người mới (dễ hiểu)

> Đọc xong file này bạn sẽ hiểu: **A7 là gì, nhận từ đâu, gửi đi đâu, và con bot
> Telegram hoạt động ra sao.** Không cần biết code trước.

---

## 1. A7 là cái gì? (1 câu)

**A7 là "anh đưa tin" của hệ thống.** Khi có chuyện cần báo (cháy, CO2 cao,
người lạ vào cửa…), A7 nhận tin đó rồi **gửi cảnh báo ra Telegram / Email / ghi log**
cho con người biết.

> Ví dụ đời thường: A7 giống **lễ tân toà nhà**. Bộ phận an ninh (A6) gọi điện
> báo "tầng 3 có khói!", lễ tân (A7) lập tức **nhắn tin cho mọi người** qua các
> kênh đã hẹn trước. Lễ tân không tự đi kiểm tra khói — chỉ lo việc **báo tin**.

---

## 2. A7 nhận dữ liệu TỪ ĐÂU?

Chỉ có **1 nguồn duy nhất: nhóm A6 (Core Business)** gửi sang.

- A6 là "bộ não" — nó nhận dữ liệu cảm biến (từ A1), camera (A4), cửa (A3)…
  và **quyết định** cái nào đáng báo động.
- Khi A6 thấy có chuyện, nó **gọi sang A7 qua mạng (REST API)**, cụ thể là gửi
  một gói tin tới địa chỉ:

```
POST  http://<IP-máy-A7>:8000/api/v1/alerts
```

> Hiểu nôm na: A6 "điền vào tờ giấy báo cáo" rồi **nhét qua khe cửa** của A7.
> A7 nhận tờ giấy đó.

### Tờ giấy báo cáo đó trông như thế nào? (A6 gửi gì)
A6 gửi một gói JSON. Bắt buộc có 3 ô, còn lại tuỳ chọn:

| Ô | Bắt buộc? | Ý nghĩa | Ví dụ |
|---|---|---|---|
| `title` | ✅ | Tiêu đề ngắn | `"🚨 NGUY HIỂM — phòng Lab 2"` |
| `message` | ✅ | Nội dung chi tiết | `"Nhiệt độ 42°C, có khói"` |
| `severity` | ✅ | Mức độ: `low` / `medium` / `high` | `"high"` |
| `source_service` | ⬜ | Ai gửi | `"team-core"` |
| `event_id` | ⬜ | Mã sự kiện (để chống gửi trùng) | `"core-abc123"` |
| `location` | ⬜ | Vị trí | `"Tầng 3"` |
| `channels` | ⬜ | Ép gửi qua kênh nào | `["telegram"]` |

---

## 3. A7 gửi đi ĐÂU? (3 kênh)

A7 có thể báo ra **3 kênh**:

| Kênh | Là gì | Trạng thái hiện tại |
|---|---|---|
| 📱 **Telegram** | Nhắn vào group/chat Telegram qua con bot | ✅ **Đã cấu hình, chạy được** |
| 📧 **Email** | Gửi mail | ⬜ Để trống (chưa cấu hình SMTP) |
| 📝 **Log** | Ghi ra màn hình/log của service | ✅ **Luôn chạy** (kênh an toàn nhất) |

**Không phải tin nào cũng gửi cả 3 kênh.** A7 chọn kênh theo **mức độ nghiêm trọng**
(severity) như sau:

| severity | Gửi qua kênh nào | Ý nghĩa |
|---|---|---|
| `high` (cao) | 📱 Telegram + 📧 Email + 📝 Log | Khẩn cấp → báo tất cả |
| `medium` (vừa) | 📧 Email + 📝 Log | Vừa phải |
| `low` (thấp) | 📝 Log | Chỉ ghi lại |

> Quy tắc này nằm trong [channels.py](src/notify_app/channels.py) (`DEFAULT_ROUTING`).
> Nếu A6 tự chỉ định ô `channels` thì A7 nghe theo A6; không thì dùng bảng trên.

---

## 4. Con bot Telegram hoạt động thế nào? (phần bạn hỏi)

Đây là cách A7 nhắn được vào Telegram. Cần đúng **2 thứ**:

```
TELEGRAM_BOT_TOKEN   ← "chìa khoá" của con bot (ai cầm thì điều khiển được bot)
TELEGRAM_CHAT_ID     ← "địa chỉ" của người/group sẽ nhận tin
```

Cả hai để trong file [.env](.env):
```
TELEGRAM_BOT_TOKEN=8885718148:AAFJoEgou10UtkK8XiDcayCrnqGzQaBmWk4
TELEGRAM_CHAT_ID=6056137626
```

### Lấy 2 thứ này ở đâu?
1. **BOT_TOKEN** — nhắn cho **@BotFather** trên Telegram, gõ `/newbot`, đặt tên →
   BotFather đưa cho một chuỗi token. Đó là chìa khoá bot.
2. **CHAT_ID** — nhắn cho **@userinfobot**, nó trả về con số `chat_id` của bạn.
   Đó là "địa chỉ nhà" để bot biết gửi tin cho ai.

> ⚠️ Trước khi bot nhắn được cho bạn, **bạn phải bấm Start / nhắn cho bot 1 lần**
> trước (Telegram không cho người lạ nhắn trước). Đây là lỗi hay gặp nhất.

### Khi gửi, A7 làm gì?
A7 gọi tới máy chủ Telegram bằng đúng token + chat_id:
```
POST https://api.telegram.org/bot<TOKEN>/sendMessage
{ "chat_id": <CHAT_ID>, "text": "[HIGH] 🚨 NGUY HIỂM\nNhiệt độ 42°C, có khói" }
```
Telegram nhận xong → tin nhắn hiện lên điện thoại bạn. Xong!
(Code ở hàm `send_telegram` trong [channels.py](src/notify_app/channels.py).)

---

## 5. Toàn bộ luồng đi của 1 cảnh báo (sơ đồ)

```
  Cảm biến/Camera/Cửa
        │  (dữ liệu thô)
        ▼
   ┌─────────┐  thấy nguy hiểm   ┌─────────┐   chọn kênh    📱 Telegram
   │   A6    │ ───────────────►  │   A7    │ ─────────────► 📧 Email
   │ (bộ não)│   POST /alerts    │(đưa tin)│                📝 Log
   └─────────┘                   └─────────┘
                                      │
                                  trả lời ngay: "202 Accepted"
                                  (A7 nhận rồi, gửi kênh ở phía sau)
```

**Điểm quan trọng:** A7 nhận tin xong là **trả lời "OK, nhận rồi" (202) ngay lập tức**,
rồi mới đi gửi Telegram/Email ở phía sau. Lý do: để A6 **không phải đứng chờ** —
nếu Telegram chậm thì cũng không làm nghẽn A6.

---

## 6. Hai "mẹo thông minh" của A7 (để khỏi bị quê khi thầy hỏi)

1. **Chống gửi trùng (dedup):** nếu cùng một `event_id` được gửi 2 lần (do mạng
   gửi lại), A7 **chỉ gửi 1 lần**, lần sau trả `"duplicate"`. → không spam.

2. **Một kênh lỗi không làm chết cả service:** nếu Telegram lỗi, A7 vẫn ghi Log
   và gửi Email bình thường. Không bao giờ crash vì 1 kênh hỏng.

---

## 7. Cách chạy & test nhanh (copy-paste)

**Bật service:**
```powershell
cd E:\baitap1\demo-day-team-notify
docker compose up -d --build
```

**Kiểm tra sống chưa:**
```powershell
curl http://localhost:8000/health
```
→ `{"status":"ok","service":"notification","version":"1.0.0"}`

**Bắn thử 1 cảnh báo (giả làm A6) → kiểm tra Telegram có nhận không:**
```powershell
curl -X POST http://localhost:8000/api/v1/alerts -H "Content-Type: application/json" -d "{\"title\":\"Test canh bao\",\"message\":\"Day la tin thu nghiem\",\"severity\":\"high\"}"
```
→ A7 trả `202 accepted` + điện thoại bạn **kêu tin Telegram**.
(Hoặc dùng sẵn script: `python tools\mock_core_send.py`.)

**Xem log A7 đã làm gì:**
```powershell
docker compose logs -f
```
→ thấy dòng `[NOTIFY:telegram] đã gửi`.

---

## 8. Tóm tắt 30 giây (học thuộc đoạn này là trả lời được thầy)

> "A7 là service **thông báo**. Nó **nhận cảnh báo từ A6** qua REST
> (`POST /api/v1/alerts`), rồi **gửi ra Telegram / Email / Log** tuỳ mức độ
> nghiêm trọng: `high` báo cả 3 kênh, `medium` email+log, `low` chỉ log. Telegram
> chạy bằng **bot token + chat_id** cấu hình trong `.env`. A7 nhận xong **trả 202
> ngay** rồi gửi kênh ở nền, có **chống trùng** và **một kênh lỗi không làm sập** service."
