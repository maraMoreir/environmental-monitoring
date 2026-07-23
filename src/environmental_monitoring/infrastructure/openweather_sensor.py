"""Real air-quality data source via the OpenWeatherMap Air Pollution API.

Unlike `SimulatedSensor`, this `ReadingSource` fetches actual measured
PM2.5/PM10 concentrations for a given latitude/longitude — it's the concrete
example behind the "swap the data source without touching the rest of the
pipeline" claim in docs/ARCHITECTURE.md.

Free tier: https://openweathermap.org/api/air-pollution — sign up for an API
key and set `ENVMON_OPENWEATHER_API_KEY`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import requests

from environmental_monitoring.domain.models import SensorReading

_API_URL = "https://api.openweathermap.org/data/2.5/air_pollution"
_REQUEST_TIMEOUT_SECONDS = 10


class OpenWeatherAirQualitySensor:
    """`ReadingSource` backed by real, currently-measured air-quality data."""

    def __init__(
        self,
        sensor_id: str,
        api_key: str,
        latitude: float,
        longitude: float,
        *,
        session: requests.Session | None = None,
    ) -> None:
        self._sensor_id = sensor_id
        self._api_key = api_key
        self._latitude = latitude
        self._longitude = longitude
        self._session = session or requests.Session()

    def read(self) -> SensorReading:
        response = self._session.get(
            _API_URL,
            params={
                "lat": str(self._latitude),
                "lon": str(self._longitude),
                "appid": self._api_key,
            },
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return self._to_reading(response.json())

    def _to_reading(self, payload: dict[str, Any]) -> SensorReading:
        entry = payload["list"][0]
        components = entry["components"]
        return SensorReading(
            sensor_id=self._sensor_id,
            timestamp=datetime.fromtimestamp(entry["dt"], tz=UTC),
            pm2_5=float(components["pm2_5"]),
            pm10=float(components["pm10"]),
            # The air-pollution endpoint doesn't report temperature/humidity;
            # SensorReading treats both as optional for exactly this reason.
        )
