from __future__ import annotations

from collections.abc import Iterator

import pytest
from pydantic import ValidationError

from environmental_monitoring.config import Settings, get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> Iterator[None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_defaults_target_the_local_demo_stack() -> None:
    settings = Settings(_env_file=None)

    assert settings.mqtt_broker_host == "localhost"
    assert settings.aws_iot_enabled is False
    assert settings.dashboard_port == 8050


def test_env_vars_override_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENVMON_MQTT_BROKER_HOST", "mosquitto")
    monkeypatch.setenv("ENVMON_DASHBOARD_PORT", "9000")

    settings = get_settings()

    assert settings.mqtt_broker_host == "mosquitto"
    assert settings.dashboard_port == 9000


def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()


def test_aws_iot_enabled_without_endpoint_fails_fast() -> None:
    with pytest.raises(ValidationError, match="ENVMON_AWS_IOT_ENDPOINT"):
        Settings(_env_file=None, aws_iot_enabled=True, aws_iot_endpoint="")


def test_sensor_location_label_joins_city_state_country() -> None:
    settings = Settings(
        _env_file=None, sensor_city="São Paulo", sensor_state="SP", sensor_country="Brazil"
    )

    assert settings.sensor_location_label == "São Paulo, SP, Brazil"


def test_sensor_location_label_skips_empty_parts() -> None:
    settings = Settings(
        _env_file=None, sensor_city="Berlin", sensor_state="", sensor_country="Germany"
    )

    assert settings.sensor_location_label == "Berlin, Germany"
