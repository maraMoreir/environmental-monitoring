from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import requests

from environmental_monitoring.infrastructure.openweather_sensor import OpenWeatherAirQualitySensor

_POLLUTION_PAYLOAD = {
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

_WEATHER_PAYLOAD = {"main": {"temp": 24.5, "humidity": 61, "pressure": 1013}, "name": "Sao Paulo"}


def _mock_response(payload: dict) -> MagicMock:
    response = MagicMock()
    response.json.return_value = payload
    return response


def _make_sensor(
    *,
    pollution_response: MagicMock | None = None,
    weather_response: MagicMock | None = None,
    weather_raises: Exception | None = None,
) -> tuple[OpenWeatherAirQualitySensor, MagicMock]:
    session = MagicMock(spec=requests.Session)
    resolved_pollution_response = pollution_response or _mock_response(_POLLUTION_PAYLOAD)
    resolved_weather_response = weather_response or _mock_response(_WEATHER_PAYLOAD)

    def _get(url: str, **_kwargs: object) -> MagicMock:
        if "air_pollution" in url:
            return resolved_pollution_response
        if weather_raises is not None:
            raise weather_raises
        return resolved_weather_response

    session.get.side_effect = _get
    sensor = OpenWeatherAirQualitySensor(
        sensor_id="sensor-001",
        api_key="test-key",
        latitude=-23.55,
        longitude=-46.63,
        session=session,
    )
    return sensor, session


def test_read_parses_pm_and_weather_values() -> None:
    sensor, _ = _make_sensor()

    reading = sensor.read()

    assert reading.sensor_id == "sensor-001"
    assert reading.pm2_5 == 12.3
    assert reading.pm10 == 18.9
    assert reading.temperature_celsius == 24.5
    assert reading.humidity_percent == 61.0


def test_read_calls_pollution_endpoint_with_expected_params() -> None:
    sensor, session = _make_sensor()

    sensor.read()

    args, kwargs = session.get.call_args_list[0]
    assert "air_pollution" in args[0]
    assert kwargs["params"] == {"lat": "-23.55", "lon": "-46.63", "appid": "test-key"}
    assert kwargs["timeout"] == 10


def test_read_calls_weather_endpoint_with_metric_units() -> None:
    sensor, session = _make_sensor()

    sensor.read()

    args, kwargs = session.get.call_args_list[1]
    assert "/weather" in args[0]
    assert kwargs["params"] == {
        "lat": "-23.55",
        "lon": "-46.63",
        "appid": "test-key",
        "units": "metric",
    }


def test_read_propagates_pollution_http_errors() -> None:
    pollution_response = _mock_response(_POLLUTION_PAYLOAD)
    pollution_response.raise_for_status.side_effect = requests.HTTPError("401 Unauthorized")
    sensor, _ = _make_sensor(pollution_response=pollution_response)

    with pytest.raises(requests.HTTPError):
        sensor.read()


def test_read_survives_weather_http_error_and_leaves_weather_fields_none() -> None:
    weather_response = _mock_response(_WEATHER_PAYLOAD)
    weather_response.raise_for_status.side_effect = requests.HTTPError("429 Too Many Requests")
    sensor, _ = _make_sensor(weather_response=weather_response)

    reading = sensor.read()

    assert reading.pm2_5 == 12.3  # air quality reading is unaffected
    assert reading.temperature_celsius is None
    assert reading.humidity_percent is None


def test_read_survives_weather_connection_error() -> None:
    sensor, _ = _make_sensor(weather_raises=requests.ConnectionError("network unreachable"))

    reading = sensor.read()

    assert reading.pm2_5 == 12.3
    assert reading.temperature_celsius is None
    assert reading.humidity_percent is None
