"""Runtime configuration, sourced from environment variables / a `.env` file.

Nothing here defaults to a real secret: AWS credentials are intentionally
absent (boto3's default credential chain handles those — see
`infrastructure/aws_iot.py`) and every other default targets the local
Docker Compose demo.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ENVMON_", env_file=".env", extra="ignore")

    mqtt_broker_host: str = "localhost"
    mqtt_broker_port: int = 1883
    mqtt_topic: str = "sensors/readings"
    mqtt_use_tls: bool = False
    mqtt_ca_cert_path: str | None = None

    aws_iot_enabled: bool = False
    aws_iot_topic: str = "sensors/readings"
    aws_region: str = "us-east-1"
    aws_iot_endpoint: str = ""

    database_path: str = "data/readings.db"
    dashboard_port: int = 8050
    api_port: int = 8000
    debug: bool = False

    sensor_id: str = "sensor-001"
    publish_interval_seconds: float = 5.0
    sensor_city: str = "São Paulo"
    sensor_state: str = "SP"
    sensor_country: str = "Brazil"

    openweather_api_key: str = ""
    openweather_latitude: float = 0.0
    openweather_longitude: float = 0.0

    @model_validator(mode="after")
    def _require_endpoint_when_aws_iot_enabled(self) -> Self:
        if self.aws_iot_enabled and not self.aws_iot_endpoint:
            raise ValueError("ENVMON_AWS_IOT_ENDPOINT must be set when ENVMON_AWS_IOT_ENABLED=true")
        return self

    @property
    def sensor_location_label(self) -> str:
        """Human-readable "City, State, Country" for display, skipping empty parts."""
        return ", ".join(
            part for part in (self.sensor_city, self.sensor_state, self.sensor_country) if part
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
