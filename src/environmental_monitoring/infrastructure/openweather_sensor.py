"""Real air-quality data source via the OpenWeatherMap APIs.

Unlike `SimulatedSensor`, this `ReadingSource` fetches actual measured
PM2.5/PM10 concentrations (Air Pollution API) and temperature/humidity
(Current Weather API) for a given latitude/longitude. It's the concrete
example referenced throughout the docs: swapping data sources means writing
one new `ReadingSource` adapter, nothing else in the pipeline changes.

Free tier: https://openweathermap.org/api/air-pollution and
https://openweathermap.org/current — sign up for an API key and set
`ENVMON_OPENWEATHER_API_KEY`.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import requests

from environmental_monitoring.domain.models import SensorReading

_AIR_POLLUTION_URL = "https://api.openweathermap.org/data/2.5/air_pollution"
_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
_REQUEST_TIMEOUT_SECONDS = 10

logger = logging.getLogger(__name__)


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
        pollution_response = self._session.get(
            _AIR_POLLUTION_URL,
            params=self._location_params(),
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
        pollution_response.raise_for_status()
        entry = pollution_response.json()["list"][0]
        components = entry["components"]

        temperature_celsius, humidity_percent = self._fetch_weather()

        return SensorReading(
            sensor_id=self._sensor_id,
            timestamp=datetime.fromtimestamp(entry["dt"], tz=UTC),
            pm2_5=float(components["pm2_5"]),
            pm10=float(components["pm10"]),
            temperature_celsius=temperature_celsius,
            humidity_percent=humidity_percent,
        )

    def _fetch_weather(self) -> tuple[float | None, float | None]:
        """Best-effort: PM2.5/PM10 is this adapter's primary purpose, so a
        failure here shouldn't discard an otherwise-good air-quality reading.
        """
        try:
            response = self._session.get(
                _WEATHER_URL,
                params={**self._location_params(), "units": "metric"},
                timeout=_REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            main = response.json()["main"]
            return float(main["temp"]), float(main["humidity"])
        except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
            logger.warning(
                "Failed to fetch temperature/humidity for sensor %s: %s", self._sensor_id, exc
            )
            return None, None

    def _location_params(self) -> dict[str, Any]:
        return {"lat": str(self._latitude), "lon": str(self._longitude), "appid": self._api_key}
