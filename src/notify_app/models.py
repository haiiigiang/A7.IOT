from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class AlertRequest(BaseModel):
    """Payload A6 (Core) gửi sang A7 — theo Contract_A6-A7_Notification."""
    title: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    severity: Severity
    # Các field khuyến nghị / tùy chọn
    source_service: Optional[str] = None
    event_id: Optional[str] = None
    timestamp: Optional[str] = None
    location: Optional[str] = None
    channels: Optional[List[str]] = None


class AlertAccepted(BaseModel):
    status: str
    notification_id: str
    received_event_id: Optional[str] = None
    channels: List[str]


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
