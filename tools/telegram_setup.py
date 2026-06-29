"""Trợ giúp cấu hình Telegram cho Notification Service (A7).

Dùng để: (1) tìm chat_id tự động, (2) gửi tin nhắn thử.
Chỉ dùng thư viện chuẩn (urllib), không cần cài thêm.

QUY TRÌNH:
  1) Mở Telegram -> tìm @BotFather -> /newbot -> đặt tên -> lấy TOKEN.
  2) Tìm đúng bot vừa tạo, bấm START (hoặc gửi 1 tin nhắn bất kỳ cho nó).
  3) Lấy chat_id:
       python tools/telegram_setup.py --token <TOKEN>
  4) Gửi thử (sau khi đã có chat_id):
       python tools/telegram_setup.py --token <TOKEN> --chat-id <CHAT_ID> --send
"""
import argparse
import json
import urllib.request


def _api(token: str, method: str, params: dict | None = None):
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = None
    headers = {}
    if params is not None:
        data = json.dumps(params).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers,
                                 method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def find_chat_ids(token: str):
    res = _api(token, "getUpdates")
    if not res.get("ok"):
        print("[ERROR] Token sai hoac loi API:", res)
        return
    updates = res.get("result", [])
    if not updates:
        print("Chua thay tin nhan nao.")
        print("=> Hay mo Telegram, tim bot cua ban, bam START / gui 1 tin nhan, roi chay lai.")
        return
    seen = {}
    for u in updates:
        msg = u.get("message") or u.get("edited_message") or {}
        chat = msg.get("chat") or {}
        cid = chat.get("id")
        if cid is not None and cid not in seen:
            name = chat.get("title") or chat.get("username") or chat.get("first_name") or "?"
            seen[cid] = name
    print("=== chat_id tim thay ===")
    for cid, name in seen.items():
        print(f"  chat_id = {cid}   (chat: {name})")
    print()
    print("Dien vao .env:")
    for cid in seen:
        print(f"  TELEGRAM_BOT_TOKEN=<token cua ban>")
        print(f"  TELEGRAM_CHAT_ID={cid}")
        break


def send_test(token: str, chat_id: str):
    res = _api(token, "sendMessage", {
        "chat_id": chat_id,
        "text": "[TEST] Notification Service (A7) da ket noi Telegram thanh cong!",
    })
    if res.get("ok"):
        print("[OK] Da gui tin nhan thu. Kiem tra Telegram cua ban.")
    else:
        print("[ERROR] Gui that bai:", res)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", required=True, help="Bot token tu @BotFather")
    ap.add_argument("--chat-id", default=None)
    ap.add_argument("--send", action="store_true", help="Gui tin nhan thu (can --chat-id)")
    args = ap.parse_args()

    if args.send:
        if not args.chat_id:
            print("[ERROR] Can --chat-id de gui thu.")
            return
        send_test(args.token, args.chat_id)
    else:
        find_chat_ids(args.token)


if __name__ == "__main__":
    main()
