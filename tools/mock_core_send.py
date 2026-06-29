"""Mock A6 (Core Business): gửi alert thử sang Notification (A7).

Dùng để test A7 độc lập khi nhóm Core chưa sẵn sàng.
Chỉ dùng thư viện chuẩn (urllib) nên không cần cài thêm gì.

Ví dụ:
    python tools/mock_core_send.py
    python tools/mock_core_send.py --severity medium --title "Khói" --message "Phòng B201 có khói"
    python tools/mock_core_send.py --url http://26.31.10.34:8000/api/v1/alerts   # gọi qua Radmin IP
"""
import argparse
import json
import urllib.request
from uuid import uuid4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000/api/v1/alerts")
    ap.add_argument("--severity", default="high", choices=["low", "medium", "high"])
    ap.add_argument("--title", default="Cảnh báo thử nghiệm")
    ap.add_argument("--message", default="Đây là alert mock từ Core (A6).")
    ap.add_argument("--channels", default=None,
                    help="Danh sách kênh, phân tách bởi dấu phẩy, vd: log,telegram")
    args = ap.parse_args()

    payload = {
        "title": args.title,
        "message": args.message,
        "severity": args.severity,
        "source_service": "team-core",
        "event_id": f"mock-{uuid4().hex[:8]}",
    }
    if args.channels:
        payload["channels"] = [c.strip() for c in args.channels.split(",") if c.strip()]

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        args.url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    print(">> POST", args.url)
    print("   body:", json.dumps(payload, ensure_ascii=False))
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f"<< {resp.status} {resp.read().decode()}")
    except urllib.error.HTTPError as e:
        print(f"<< {e.code} {e.read().decode()}")
    except Exception as e:  # noqa: BLE001
        print(f"[ERROR] Loi goi service: {e}")


if __name__ == "__main__":
    main()
