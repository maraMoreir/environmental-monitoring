from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import requests

from environmental_monitoring.infrastructure.openweather_sensor import OpenWeatherAirQualitySensor

_SAMPLE_PAYLOAD = {
    "coord": {"lon": -46.63, "lat": -23.55},
    "list": [
        {
            "dt": 1706000000,
            "main": {"aqi": 2},
            "components": {
                "co": 200.1,
                "no": 0.5,
                "no2": 10.2,
                "o3": 68.7,
                "so2": 2.1,
                "pm2_5": 12.3,
                "pm10": 18.9,
                "nh3": 1.0,
            },
        }
    ],
}


def _make_sensor() -> tuple[OpenWeatherAirQualitySensor, MagicMock]:
    session = MagicMock(spec=requests.Session)
    sensor = OpenWeatherAirQualitySensor(
        sensor_id="sensor-001",
        api_key="test-key",
        latitude=-23.55,
        longitude=-46.63,
        session=session,
    )
    return sensor, session


def test_read_parses_pm_values_from_api_response() -> None:
    sensor, session = _make_sensor()
    response = MagicMock()
    response.json.return_value = _SAMPLE_PAYLOAD
    session.get.return_value = response

    reading = sensor.read()

    assert reading.sensor_id == "sensor-001"
    assert reading.pm2_5 == 12.3
    assert reading.pm10 == 18.9
    assert reading.temperature_celsius is None
    assert reading.humidity_percent is None
    response.raise_for_status.assert_called_once()


def test_read_calls_api_with_expected_params() -> None:
    sensor, session = _make_sensor()
    response = MagicMock()
    response.json.return_value = _SAMPLE_PAYLOAD
    session.get.return_value = response

    sensor.read()

    _, kwargs = session.get.call_args
    assert kwargs["params"] == {"lat": "-23.55", "lon": "-46.63", "appid": "test-key"}
    assert kwargs["timeout"] == 10


def test_read_propagates_http_errors() -> None:
    sensor, session = _make_sensor()
    response = MagicMock()
    response.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")
    session.get.return_value = response

    with pytest.raises(requests.HTTPError):
        sensor.read()
