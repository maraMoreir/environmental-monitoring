"""Synthetic sensor for demos and tests. There is no real hardware here.

Replaces the old dashboard's `random.uniform()` noise with a bounded random
walk so generated readings look like a plausible air-quality trend instead
of pure static, and are deterministic under a fixed seed for testing.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime

from environmental_monitoring.domain.models import SensorReading

_BASELINE_PM2_5 = 18.0
_BASELINE_PM10 = 28.0
_BASELINE_TEMPERATURE_C = 24.0
_BASELINE_HUMIDITY = 55.0


class SimulatedSensor:
    """`ReadingSource` that fabricates physically plausible air-quality data."""

    def __init__(self, sensor_id: str, *, seed: int | None = None) -> None:
        self._sensor_id = sensor_id
        self._rng = random.Random(seed)
        self._pm2_5 = _BASELINE_PM2_5
        self._pm10 = _BASELINE_PM10
        self._temperature = _BASELINE_TEMPERATURE_C
        self._humidity = _BASELINE_HUMIDITY

    def read(self) -> SensorReading:
        self._pm2_5 = _walk(self._rng, self._pm2_5, step=3.0, minimum=0.0, maximum=180.0)
        # PM10 includes PM2.5 in real particulate measurements, so keep pm10 >= pm2_5.
        self._pm10 = _walk(
            self._rng, max(self._pm10, self._pm2_5), step=3.5, minimum=self._pm2_5, maximum=250.0
        )
        self._temperature = _walk(
            self._rng, self._temperature, step=0.4, minimum=-10.0, maximum=45.0
        )
        self._humidity = _walk(self._rng, self._humidity, step=1.5, minimum=10.0, maximum=100.0)
        return SensorReading(
            sensor_id=self._sensor_id,
            timestamp=datetime.now(UTC),
            pm2_5=round(self._pm2_5, 1),
            pm10=round(self._pm10, 1),
            temperature_celsius=round(self._temperature, 1),
            humidity_percent=round(self._humidity, 1),
        )


def _walk(
    rng: random.Random, current: float, *, step: float, minimum: float, maximum: float
) -> float:
    candidate = current + rng.uniform(-step, step)
    return min(max(candidate, minimum), maximum)
