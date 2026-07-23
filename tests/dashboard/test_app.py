from __future__ import annotations

from datetime import UTC, datetime

from environmental_monitoring.dashboard.app import _build_figure, _build_summary
from environmental_monitoring.domain.models import SensorReading


def _reading(minute: int) -> SensorReading:
    return SensorReading(
        sensor_id="sensor-001",
        timestamp=datetime(2026, 1, 1, 12, minute, tzinfo=UTC),
        pm2_5=10.0 + minute,
        pm10=20.0 + minute,
    )


def test_empty_readings_shows_empty_state() -> None:
    summary = _build_summary([])

    assert len(summary) == 1
    assert "Waiting for sensor data" in summary[0].children


def test_build_figure_produces_two_labeled_traces() -> None:
    figure = _build_figure([_reading(m) for m in range(3)])

    assert len(figure.data) == 2
    assert figure.data[0].name == "PM2.5 (µg/m³)"
    assert figure.data[1].name == "PM10 (µg/m³)"


def test_summary_includes_stat_row_and_status_pill() -> None:
    readings = [_reading(m) for m in range(3)]

    stat_row, status_row = _build_summary(readings)

    assert stat_row.className == "envmon-stat-row"
    assert len(stat_row.children) == 4  # PM2.5, PM10, temperature, humidity tiles

    pill, count_line = status_row.children
    assert pill.children == "Good"
    assert "3 readings from 1 sensor(s)" in count_line.children


def test_summary_reflects_higher_pm2_5_as_worse_status() -> None:
    reading = SensorReading(
        sensor_id="sensor-001",
        timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        pm2_5=200.0,
        pm10=220.0,
    )

    _, status_row = _build_summary([reading])
    pill = status_row.children[0]

    assert pill.children == "Very unhealthy"
    assert pill.style["backgroundColor"] == "#d03b3b"
