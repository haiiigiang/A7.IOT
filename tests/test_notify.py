from fastapi.testclient import TestClient

from src.notify_app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["service"] == "notification"


def test_alert_high_accepted_and_routed():
    r = client.post("/api/v1/alerts", json={
        "title": "Cảnh báo nhiệt độ",
        "message": "Lab A101: 42C",
        "severity": "high",
        "source_service": "team-core",
    })
    assert r.status_code == 202
    body = r.json()
    assert body["status"] == "accepted"
    assert body["notification_id"].startswith("notif-")
    # high -> telegram + email + log
    assert body["channels"] == ["telegram", "email", "log"]


def test_alert_low_routes_log_only():
    r = client.post("/api/v1/alerts", json={"title": "t", "message": "m", "severity": "low"})
    assert r.status_code == 202
    assert r.json()["channels"] == ["log"]


def test_explicit_channels_override():
    r = client.post("/api/v1/alerts", json={
        "title": "t", "message": "m", "severity": "low", "channels": ["log", "telegram"],
    })
    assert r.json()["channels"] == ["log", "telegram"]


def test_missing_severity_is_422():
    r = client.post("/api/v1/alerts", json={"title": "t", "message": "m"})
    assert r.status_code == 422
    body = r.json()
    assert body["error"] == "validation_error"
    assert "severity" in body["missing_fields"]


def test_invalid_severity_is_422():
    r = client.post("/api/v1/alerts", json={"title": "t", "message": "m", "severity": "urgent"})
    assert r.status_code == 422


def test_empty_title_is_422():
    r = client.post("/api/v1/alerts", json={"title": "", "message": "m", "severity": "low"})
    assert r.status_code == 422


def test_dedup_by_event_id():
    payload = {"title": "t", "message": "m", "severity": "high", "event_id": "evt-dedup-1"}
    r1 = client.post("/api/v1/alerts", json=payload)
    r2 = client.post("/api/v1/alerts", json=payload)
    assert r1.status_code == 202
    assert r1.json()["status"] == "accepted"
    assert r2.status_code == 200
    assert r2.json()["status"] == "duplicate"
