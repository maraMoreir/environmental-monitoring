"""Command-line entrypoints for the pipeline stages: simulate, openweather, ingest.

Installed as the `envmon` console script; `monitoring.py` at the repo root is
a thin delegator to `main()` for users who haven't done an editable install.
"""

from __future__ import annotations

import argparse
import logging
import time

import requests

from environmental_monitoring.application.ports import ReadingSource
from environmental_monitoring.application.services import IngestionService
from environmental_monitoring.config import Settings, get_settings
from environmental_monitoring.domain.locations import BRAZIL_STATE_CAPITALS
from environmental_monitoring.infrastructure.aws_iot import AwsIotPublisher
from environmental_monitoring.infrastructure.mqtt_broker import MqttReadingBroker
from environmental_monitoring.infrastructure.openweather_sensor import OpenWeatherAirQualitySensor
from environmental_monitoring.infrastructure.repository import SqliteReadingRepository
from environmental_monitoring.infrastructure.simulator import SimulatedSensor

logger = logging.getLogger(__name__)

# Each sensor.read() now makes 2 API calls (air pollution + weather), so this
# paces 27 locations x 2 calls = 54 calls comfortably under OpenWeatherMap's
# free-tier 60 calls/minute limit (~43 calls/min at this delay).
_BRAZIL_INTER_CALL_DELAY_SECONDS = 2.5


def _build_broker(settings: Settings, client_id: str) -> MqttReadingBroker:
    return MqttReadingBroker(
        settings.mqtt_broker_host,
        settings.mqtt_broker_port,
        topic=settings.mqtt_topic,
        client_id=client_id,
        use_tls=settings.mqtt_use_tls,
        ca_cert_path=settings.mqtt_ca_cert_path,
    )


def _run_publish_loop(
    sensor: ReadingSource, broker: MqttReadingBroker, interval_seconds: float, label: str
) -> None:
    """Shared publish loop: any `ReadingSource` (synthetic or real) drives it identically."""
    broker.connect()
    try:
        while True:
            reading = sensor.read()
            broker.publish(reading)
            logger.info("Published %s", reading)
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        logger.info("%s stopped.", label)
    finally:
        broker.disconnect()


def run_simulate(settings: Settings) -> None:
    """Generate synthetic readings and publish them over MQTT, like a real sensor would."""
    sensor = SimulatedSensor(settings.sensor_id)
    broker = _build_broker(settings, client_id=f"simulator-{settings.sensor_id}")
    logger.info(
        "Publishing simulated readings for %s to %s:%s/%s",
        settings.sensor_id,
        settings.mqtt_broker_host,
        settings.mqtt_broker_port,
        settings.mqtt_topic,
    )
    _run_publish_loop(sensor, broker, settings.publish_interval_seconds, "Simulator")


def _require_openweather_api_key(settings: Settings, mode: str) -> None:
    if not settings.openweather_api_key:
        raise SystemExit(
            f"ENVMON_OPENWEATHER_API_KEY is required for --mode {mode} "
            "(get a free key at https://openweathermap.org/api/air-pollution)"
        )


def run_openweather(settings: Settings) -> None:
    """Poll real air-quality data from OpenWeatherMap for one location and publish over MQTT."""
    _require_openweather_api_key(settings, "openweather")
    sensor = OpenWeatherAirQualitySensor(
        sensor_id=settings.sensor_id,
        api_key=settings.openweather_api_key,
        latitude=settings.openweather_latitude,
        longitude=settings.openweather_longitude,
    )
    broker = _build_broker(settings, client_id=f"openweather-{settings.sensor_id}")
    logger.info(
        "Publishing real OpenWeatherMap air-quality readings for (%s, %s) to %s:%s/%s",
        settings.openweather_latitude,
        settings.openweather_longitude,
        settings.mqtt_broker_host,
        settings.mqtt_broker_port,
        settings.mqtt_topic,
    )
    _run_publish_loop(sensor, broker, settings.publish_interval_seconds, "OpenWeatherMap publisher")


def run_openweather_brazil(settings: Settings) -> None:
    """Poll real air-quality data for all 27 Brazilian state capitals and publish over MQTT.

    One process, one MQTT connection, N `OpenWeatherAirQualitySensor` instances (one per
    capital) — each publish round spaces the per-location reads out by
    `_BRAZIL_INTER_CALL_DELAY_SECONDS` to stay well under OpenWeatherMap's rate limit (each
    read is itself 2 API calls: air pollution + weather), then sleeps out the rest of
    `publish_interval_seconds` before the next round.
    """
    _require_openweather_api_key(settings, "openweather-br")
    sensors = [
        (
            location.label,
            OpenWeatherAirQualitySensor(
                sensor_id=location.sensor_id,
                api_key=settings.openweather_api_key,
                latitude=location.latitude,
                longitude=location.longitude,
            ),
        )
        for location in BRAZIL_STATE_CAPITALS
    ]
    broker = _build_broker(settings, client_id="openweather-brazil")
    broker.connect()
    logger.info(
        "Publishing real OpenWeatherMap air-quality readings for %d Brazilian state "
        "capitals to %s:%s/%s every %.0fs",
        len(sensors),
        settings.mqtt_broker_host,
        settings.mqtt_broker_port,
        settings.mqtt_topic,
        settings.publish_interval_seconds,
    )
    try:
        while True:
            round_start = time.monotonic()
            for label, sensor in sensors:
                try:
                    reading = sensor.read()
                    broker.publish(reading)
                    logger.info("Published %s: %s", label, reading)
                except requests.RequestException:
                    logger.exception("Failed to fetch/publish reading for %s", label)
                time.sleep(_BRAZIL_INTER_CALL_DELAY_SECONDS)
            elapsed = time.monotonic() - round_start
            time.sleep(max(0.0, settings.publish_interval_seconds - elapsed))
    except KeyboardInterrupt:
        logger.info("Brazil-wide publisher stopped.")
    finally:
        broker.disconnect()


def run_ingest(settings: Settings) -> None:
    """Subscribe to MQTT, persist validated readings, and optionally forward to AWS IoT."""
    repository = SqliteReadingRepository(settings.database_path)
    cloud_publisher = None
    if settings.aws_iot_enabled:
        cloud_publisher = AwsIotPublisher(
            topic=settings.aws_iot_topic,
            region_name=settings.aws_region,
            endpoint_url=settings.aws_iot_endpoint,
        )
    service = IngestionService(repository, cloud_publisher)
    broker = _build_broker(settings, client_id="ingestion-service")

    logger.info(
        "Ingesting readings from %s:%s/%s into %s",
        settings.mqtt_broker_host,
        settings.mqtt_broker_port,
        settings.mqtt_topic,
        settings.database_path,
    )
    try:
        broker.subscribe(service.ingest)
    except KeyboardInterrupt:
        logger.info("Ingestion service stopped.")
    finally:
        broker.disconnect()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envmon", description="Environmental monitoring pipeline entrypoints."
    )
    parser.add_argument(
        "--mode",
        choices=["simulate", "openweather", "openweather-br", "ingest"],
        required=True,
        help="'simulate' publishes synthetic readings over MQTT; 'openweather' publishes "
        "real air-quality readings for one location; 'openweather-br' does the same for "
        "all 27 Brazilian state capitals at once; 'ingest' consumes and persists them.",
    )
    parser.add_argument("--log-level", default="INFO", help="Python logging level (default: INFO).")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=args.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    settings = get_settings()
    dispatch = {
        "simulate": run_simulate,
        "openweather": run_openweather,
        "openweather-br": run_openweather_brazil,
        "ingest": run_ingest,
    }
    dispatch[args.mode](settings)


if __name__ == "__main__":
    main()
