"""API response DTOs — kept separate from the domain model so the wire
contract can evolve independently of `SensorReading`.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from environmental_monitoring.domain.models import SensorReading


class ReadingResponse(BaseModel):
    sensor_id: str
    timestamp: datetime
    pm2_5: float
    pm10: float
    temperature_celsius: float | None
    humidity_percent: float | None
    air_quality_level: str

    @classmethod
    def from_domain(cls, reading: SensorReading) -> ReadingResponse:
        return cls(
            sensor_id=reading.sensor_id,
            timestamp=reading.timestamp,
            pm2_5=reading.pm2_5,
            pm10=reading.pm10,
            temperature_celsius=reading.temperature_celsius,
            humidity_percent=reading.humidity_percent,
            air_quality_level=reading.air_quality_level.value,
        )
