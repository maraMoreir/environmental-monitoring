from __future__ import annotations

from datetime import UTC, datetime

from environmental_monitoring.dashboard.app import (
    _build_figure,
    _build_sensor_options,
    _build_summary,
    _resolve_sensor_selection,
    _sensor_label,
)
from environmental_monitoring.domain.models import SensorReading


def _reading(minute: int, sensor_id: str = "sensor-001") -> SensorReading:
    return SensorReading(
        sensor_id=sensor_id,
        timestamp=datetime(2026, 1, 1, 12, minute, tzinfo=UTC),
        pm2_5=10.0 + minute,
        pm10=20.0 + minute,
    )


def test_empty_readings_shows_empty_state() -> None:
    summary = _build_summary([])

    assert len(summary) == 1
    assert "Aguardando dados do sensor" in summary[0].children


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
    assert pill.children == "Boa"
    assert "3 leituras" in count_line.children


def test_summary_reflects_higher_pm2_5_as_worse_status() -> None:
    reading = SensorReading(
        sensor_id="sensor-001",
        timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        pm2_5=200.0,
        pm10=220.0,
    )

    _, status_row = _build_summary([reading])
    pill = status_row.children[0]

    assert pill.children == "Muito insalubre"
    assert pill.style["backgroundColor"] == "#d03b3b"


def test_sensor_label_uses_brazil_registry_for_known_ids() -> None:
    assert _sensor_label("br-sp") == "São Paulo, SP"
    assert _sensor_label("br-rj") == "Rio de Janeiro, RJ"


def test_sensor_label_falls_back_to_default_label_for_configured_default_sensor() -> None:
    label = _sensor_label(
        "sensor-001", default_sensor_id="sensor-001", default_label="São Paulo, SP, Brazil"
    )

    assert label == "São Paulo, SP, Brazil"


def test_sensor_label_falls_back_to_raw_id_when_unknown() -> None:
    assert _sensor_label("unknown-sensor") == "unknown-sensor"


def test_build_sensor_options_labels_known_and_unknown_ids() -> None:
    options = _build_sensor_options(
        ["br-sp", "sensor-001"], default_sensor_id="sensor-001", default_label="Casa"
    )

    assert {"label": "São Paulo, SP", "value": "br-sp"} in options
    assert {"label": "Casa", "value": "sensor-001"} in options


def test_summary_uses_sensor_label_for_location() -> None:
    readings = [_reading(0, sensor_id="br-sp")]

    _, status_row = _build_summary(readings)
    count_line = status_row.children[1]

    assert "São Paulo, SP" in count_line.children


def test_resolve_sensor_selection_keeps_valid_current_value() -> None:
    assert _resolve_sensor_selection(["br-sp", "br-rj"], "br-rj") == "br-rj"


def test_resolve_sensor_selection_falls_back_to_default_when_current_is_gone() -> None:
    selection = _resolve_sensor_selection(
        ["br-sp", "sensor-001"], "br-rj", default_sensor_id="sensor-001"
    )

    assert selection == "sensor-001"


def test_resolve_sensor_selection_falls_back_to_first_when_no_default() -> None:
    assert _resolve_sensor_selection(["br-rj", "br-sp"], None) == "br-rj"


def test_resolve_sensor_selection_returns_none_when_no_sensors() -> None:
    assert _resolve_sensor_selection([], None) is None
