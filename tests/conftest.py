from __future__ import annotations

from datetime import UTC, datetime

import pytest

from environmental_monitoring.domain.models import SensorReading


@pytest.fixture
def valid_reading() -> SensorReading:
    return SensorReading(
        sensor_id="sensor-001",
        timestamp=datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC),
        pm2_5=15.5,
        pm10=22.0,
        temperature_celsius=23.5,
        humidity_percent=48.0,
    )
