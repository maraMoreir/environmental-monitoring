from __future__ import annotations

from datetime import UTC, datetime

from environmental_monitoring.dashboard.app import _build_figure_and_status
from environmental_monitoring.domain.models import SensorReading


def test_empty_readings_shows_waiting_status() -> None:
    figure, status = _build_figure_and_status([])

    assert figure.data == ()
    assert status == "Waiting for sensor data..."


def test_readings_produce_two_traces_and_a_status_summary() -> None:
    readings = [
        SensorReading(
            sensor_id="sensor-001",
            timestamp=datetime(2026, 1, 1, 12, m, tzinfo=UTC),
            pm2_5=10.0 + m,
            pm10=20.0 + m,
        )
        for m in range(3)
    ]

    figure, status = _build_figure_and_status(readings)

    assert len(figure.data) == 2
    assert figure.data[0].name == "PM2.5 (µg/m³)"
    assert "3 readings from 1 sensor(s)" in status
    assert "good" in status
