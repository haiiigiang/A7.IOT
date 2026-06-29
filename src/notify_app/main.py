import logging
import os
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .channels import dispatch, resolve_channels
from .models import AlertAccepted, AlertRequest, HealthResponse

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SERVICE_NAME = os.getenv("SERVICE_NAME", "notification")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")

app = FastAPI(
    title="FIT4110 Demo Day - Notification Service (A7)",
    version=SERVICE_VERSION,
    description="Nhận cảnh báo từ Core (A6) và gửi ra đa kênh.",
)

# Khử trùng theo event_id (bounded in-memory set)
_seen_event_ids: set[str] = set()
_MAX_SEEN = 10000


@app.exception_handler(RequestValidationError)
async def validation_handler(request, exc: RequestValidationError):
    """Định dạng lỗi 422 theo contract: {status, error, missing_fields}."""
    missing = []
    for err in exc.errors():
        loc = err.get("loc", [])
        if loc and loc[0] == "body" and len(loc) > 1:
            missing.append(str(loc[-1]))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"status": "error", "error": "validation_error", "missing_fields": missing},
    )


@app.exception_handler(Exception)
async def internal_error_handler(request, exc: Exception):
    """Định dạng lỗi 500 theo contract: {status, error, message}."""
    logger.error(f"Internal error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"status": "error", "error": "internal_error", "message": str(exc)},
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    # Endpoint bắt buộc của Demo Day
    return HealthResponse(status="ok", service=SERVICE_NAME, version=SERVICE_VERSION)


@app.post("/api/v1/alerts", status_code=status.HTTP_202_ACCEPTED)
def create_alert(alert: AlertRequest, background_tasks: BackgroundTasks):
    # Khử trùng: nếu event_id đã thấy, không gửi lại
    if alert.event_id and alert.event_id in _seen_event_ids:
        logger.info(f"Alert trùng event_id={alert.event_id}, bỏ qua")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "duplicate", "received_event_id": alert.event_id, "channels": []},
        )
    if alert.event_id:
        if len(_seen_event_ids) >= _MAX_SEEN:
            _seen_event_ids.clear()
        _seen_event_ids.add(alert.event_id)

    severity = alert.severity.value
    channels = resolve_channels(severity, alert.channels)
    notification_id = f"notif-{uuid4().hex[:8]}"

    # Trả 202 nhanh, gửi kênh ngoài ở background để không bắt A6 chờ
    background_tasks.add_task(dispatch, channels, alert.title, alert.message, severity)

    logger.info(
        f"Accepted {notification_id} severity={severity} channels={channels} "
        f"source={alert.source_service} event_id={alert.event_id}"
    )
    return AlertAccepted(
        status="accepted",
        notification_id=notification_id,
        received_event_id=alert.event_id,
        channels=channels,
    )
