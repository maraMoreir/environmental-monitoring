from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from environmental_monitoring.api.app import create_app
from environmental_monitoring.domain.models import SensorReading


class FakeRepository:
    def __init__(self, readings: list[SensorReading]) -> None:
        self._readings = readings

    def save(self, reading: SensorReading) -> None:
        self._readings.append(reading)

    def latest(self, limit: int = 100) -> list[SensorReading]:
        return self._readings[-limit:]


def _reading(minute: int) -> SensorReading:
    return SensorReading(
        sensor_id="sensor-001",
        timestamp=datetime(2026, 1, 1, 12, minute, tzinfo=UTC),
        pm2_5=10.0 + minute,
        pm10=20.0 + minute,
    )


def test_health_returns_ok() -> None:
    client = TestClient(create_app(FakeRepository([])))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_latest_readings_returns_serialized_domain_objects() -> None:
    client = TestClient(create_app(FakeRepository([_reading(m) for m in range(3)])))

    response = client.get("/readings/latest")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3
    assert body[0]["sensor_id"] == "sensor-001"
    assert body[0]["air_quality_level"] == "good"


def test_latest_readings_respects_limit_query_param() -> None:
    client = TestClient(create_app(FakeRepository([_reading(m) for m in range(5)])))

    response = client.get("/readings/latest", params={"limit": 2})

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_latest_readings_rejects_out_of_range_limit() -> None:
    client = TestClient(create_app(FakeRepository([])))

    response = client.get("/readings/latest", params={"limit": 0})

    assert response.status_code == 422
