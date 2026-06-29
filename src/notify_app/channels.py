"""Các kênh gửi cảnh báo (đa kênh) cho Notification Service.

Mỗi sender trả về True/False; KHÔNG raise ra ngoài để một kênh lỗi
không làm hỏng các kênh còn lại hoặc làm crash service.
Kênh `log` luôn hoạt động (dùng làm kênh tối thiểu/an toàn cho demo).
"""
import logging
import os
import smtplib
from email.message import EmailMessage

import httpx

logger = logging.getLogger(__name__)

# Định tuyến mặc định khi A6 không chỉ định `channels`
DEFAULT_ROUTING = {
    "high": ["telegram", "email", "log"],
    "medium": ["email", "log"],
    "low": ["log"],
}


def resolve_channels(severity: str, channels):
    """Ưu tiên `channels` do A6 chỉ định; nếu không có thì theo severity."""
    if channels:
        return list(channels)
    return DEFAULT_ROUTING.get(severity, ["log"])


def send_log(title: str, message: str, severity: str) -> bool:
    logger.info(f"[NOTIFY:log] severity={severity} | {title} | {message}")
    return True


def send_telegram(title: str, message: str, severity: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        logger.warning("[NOTIFY:telegram] thiếu TELEGRAM_BOT_TOKEN/CHAT_ID, bỏ qua kênh telegram")
        return False
    text = f"[{severity.upper()}] {title}\n{message}"
    try:
        resp = httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=5.0,
        )
        resp.raise_for_status()
        logger.info("[NOTIFY:telegram] đã gửi")
        return True
    except Exception as e:  # noqa: BLE001 - không để kênh lỗi làm crash service
        logger.error(f"[NOTIFY:telegram] gửi thất bại: {e}")
        return False


def send_email(title: str, message: str, severity: str) -> bool:
    host = os.getenv("SMTP_HOST", "")
    if not host:
        logger.warning("[NOTIFY:email] thiếu SMTP_HOST, bỏ qua kênh email")
        return False
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASSWORD", "")
    email_to = os.getenv("EMAIL_TO", "")
    email_from = os.getenv("EMAIL_FROM", user or "noreply@notification.local")
    if not email_to:
        logger.warning("[NOTIFY:email] thiếu EMAIL_TO, bỏ qua kênh email")
        return False
    try:
        msg = EmailMessage()
        msg["Subject"] = f"[{severity.upper()}] {title}"
        msg["From"] = email_from
        msg["To"] = email_to
        msg.set_content(message)
        with smtplib.SMTP(host, port, timeout=5.0) as server:
            server.starttls()
            if user and password:
                server.login(user, password)
            server.send_message(msg)
        logger.info("[NOTIFY:email] đã gửi")
        return True
    except Exception as e:  # noqa: BLE001
        logger.error(f"[NOTIFY:email] gửi thất bại: {e}")
        return False


SENDERS = {
    "log": send_log,
    "telegram": send_telegram,
    "email": send_email,
}


def dispatch(channels, title: str, message: str, severity: str) -> dict:
    """Gửi ra từng kênh, trả về dict {channel: success_bool}."""
    results = {}
    for ch in channels:
        sender = SENDERS.get(ch)
        if sender is None:
            logger.warning(f"[NOTIFY] kênh không hỗ trợ: {ch}")
            results[ch] = False
            continue
        results[ch] = sender(title, message, severity)
    logger.info(f"[NOTIFY] kết quả gửi: {results}")
    return results
