"""Core domain model: a validated environmental sensor reading."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from environmental_monitoring.domain.exceptions import InvalidReadingError

_MAX_PARTICULATE_UGM3 = 1000.0
_MIN_TEMPERATURE_C = -50.0
_MAX_TEMPERATURE_C = 80.0


class AirQualityLevel(StrEnum):
    """Simplified US EPA AQI categories, classified from PM2.5 concentration."""

    GOOD = "good"
    MODERATE = "moderate"
    UNHEALTHY_FOR_SENSITIVE_GROUPS = "unhealthy_for_sensitive_groups"
    UNHEALTHY = "unhealthy"
    VERY_UNHEALTHY = "very_unhealthy"
    HAZARDOUS = "hazardous"

    @classmethod
    def from_pm2_5(cls, pm2_5: float) -> AirQualityLevel:
        """Classify a PM2.5 concentration (µg/m³) using simplified EPA breakpoints."""
        if pm2_5 <= 12.0:
            return cls.GOOD
        if pm2_5 <= 35.4:
            return cls.MODERATE
        if pm2_5 <= 55.4:
            return cls.UNHEALTHY_FOR_SENSITIVE_GROUPS
        if pm2_5 <= 150.4:
            return cls.UNHEALTHY
        if pm2_5 <= 250.4:
            return cls.VERY_UNHEALTHY
        return cls.HAZARDOUS


@dataclass(frozen=True, slots=True)
class SensorReading:
    """A single, validated environmental measurement from one sensor."""

    sensor_id: str
    timestamp: datetime
    pm2_5: float
    pm10: float
    temperature_celsius: float | None = None
    humidity_percent: float | None = None

    def __post_init__(self) -> None:
        if not self.sensor_id.strip():
            raise InvalidReadingError("sensor_id must not be empty")
        if self.timestamp.tzinfo is None:
            raise InvalidReadingError("timestamp must be timezone-aware")
        _require_range("pm2_5", self.pm2_5, 0.0, _MAX_PARTICULATE_UGM3)
        _require_range("pm10", self.pm10, 0.0, _MAX_PARTICULATE_UGM3)
        if self.temperature_celsius is not None:
            _require_range(
                "temperature_celsius",
                self.temperature_celsius,
                _MIN_TEMPERATURE_C,
                _MAX_TEMPERATURE_C,
            )
        if self.humidity_percent is not None:
            _require_range("humidity_percent", self.humidity_percent, 0.0, 100.0)

    @property
    def air_quality_level(self) -> AirQualityLevel:
        return AirQualityLevel.from_pm2_5(self.pm2_5)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to plain primitives, reusable by any transport/storage adapter."""
        return {
            "sensor_id": self.sensor_id,
            "timestamp": self.timestamp.isoformat(),
            "pm2_5": self.pm2_5,
            "pm10": self.pm10,
            "temperature_celsius": self.temperature_celsius,
            "humidity_percent": self.humidity_percent,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SensorReading:
        timestamp = data["timestamp"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        return cls(
            sensor_id=data["sensor_id"],
            timestamp=timestamp,
            pm2_5=float(data["pm2_5"]),
            pm10=float(data["pm10"]),
            temperature_celsius=_optional_float(data.get("temperature_celsius")),
            humidity_percent=_optional_float(data.get("humidity_percent")),
        )


def _require_range(field_name: str, value: float, minimum: float, maximum: float) -> None:
    if not minimum <= value <= maximum:
        raise InvalidReadingError(
            f"{field_name}={value} is outside the valid range [{minimum}, {maximum}]"
        )


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)
