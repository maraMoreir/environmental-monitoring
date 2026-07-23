from __future__ import annotations

from datetime import UTC, datetime

import pytest

from environmental_monitoring.domain.exceptions import InvalidReadingError
from environmental_monitoring.domain.models import AirQualityLevel, SensorReading


def test_to_dict_from_dict_roundtrip(valid_reading: SensorReading) -> None:
    assert SensorReading.from_dict(valid_reading.to_dict()) == valid_reading


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("sensor_id", ""),
        ("sensor_id", "   "),
        ("pm2_5", -1.0),
        ("pm2_5", 1001.0),
        ("pm10", -1.0),
        ("temperature_celsius", -51.0),
        ("temperature_celsius", 81.0),
        ("humidity_percent", -1.0),
        ("humidity_percent", 100.1),
    ],
)
def test_rejects_invalid_field_values(field: str, value: object) -> None:
    kwargs = dict(
        sensor_id="sensor-001",
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        pm2_5=10.0,
        pm10=15.0,
    )
    kwargs[field] = value
    with pytest.raises(InvalidReadingError):
        SensorReading(**kwargs)


def test_rejects_naive_timestamp() -> None:
    with pytest.raises(InvalidReadingError, match="timezone-aware"):
        SensorReading(
            sensor_id="sensor-001",
            timestamp=datetime(2026, 1, 1),  # noqa: DTZ001 - intentionally naive
            pm2_5=10.0,
            pm10=15.0,
        )


@pytest.mark.parametrize(
    ("pm2_5", "expected"),
    [
        (0.0, AirQualityLevel.GOOD),
        (12.0, AirQualityLevel.GOOD),
        (12.1, AirQualityLevel.MODERATE),
        (35.4, AirQualityLevel.MODERATE),
        (35.5, AirQualityLevel.UNHEALTHY_FOR_SENSITIVE_GROUPS),
        (55.5, AirQualityLevel.UNHEALTHY),
        (150.5, AirQualityLevel.VERY_UNHEALTHY),
        (250.5, AirQualityLevel.HAZARDOUS),
    ],
)
def test_air_quality_level_classification(pm2_5: float, expected: AirQualityLevel) -> None:
    reading = SensorReading(
        sensor_id="sensor-001", timestamp=datetime(2026, 1, 1, tzinfo=UTC), pm2_5=pm2_5, pm10=pm2_5
    )
    assert reading.air_quality_level == expected


def test_from_dict_accepts_string_timestamp(valid_reading: SensorReading) -> None:
    data = valid_reading.to_dict()
    assert isinstance(data["timestamp"], str)
    assert SensorReading.from_dict(data).timestamp == valid_reading.timestamp
