"""Command-line entrypoints for the two pipeline stages: simulate and ingest.

Installed as the `envmon` console script; `monitoring.py` at the repo root is
a thin delegator to `main()` for users who haven't done an editable install.
"""

from __future__ import annotations

import argparse
import logging
import time

from environmental_monitoring.application.services import IngestionService
from environmental_monitoring.config import Settings, get_settings
from environmental_monitoring.infrastructure.aws_iot import AwsIotPublisher
from environmental_monitoring.infrastructure.mqtt_broker import MqttReadingBroker
from environmental_monitoring.infrastructure.repository import SqliteReadingRepository
from environmental_monitoring.infrastructure.simulator import SimulatedSensor

logger = logging.getLogger(__name__)


def _build_broker(settings: Settings, client_id: str) -> MqttReadingBroker:
    return MqttReadingBroker(
        settings.mqtt_broker_host,
        settings.mqtt_broker_port,
        topic=settings.mqtt_topic,
        client_id=client_id,
        use_tls=settings.mqtt_use_tls,
        ca_cert_path=settings.mqtt_ca_cert_path,
    )


def run_simulate(settings: Settings) -> None:
    """Generate synthetic readings and publish them over MQTT, like a real sensor would."""
    sensor = SimulatedSensor(settings.sensor_id)
    broker = _build_broker(settings, client_id=f"simulator-{settings.sensor_id}")
    broker.connect()
    logger.info(
        "Publishing simulated readings for %s to %s:%s/%s",
        settings.sensor_id,
        settings.mqtt_broker_host,
        settings.mqtt_broker_port,
        settings.mqtt_topic,
    )
    try:
        while True:
            reading = sensor.read()
            broker.publish(reading)
            logger.info("Published %s", reading)
            time.sleep(settings.simulation_interval_seconds)
    except KeyboardInterrupt:
        logger.info("Simulator stopped.")
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
        choices=["simulate", "ingest"],
        required=True,
        help="'simulate' publishes synthetic readings over MQTT; "
        "'ingest' consumes and persists them.",
    )
    parser.add_argument("--log-level", default="INFO", help="Python logging level (default: INFO).")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=args.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    settings = get_settings()
    if args.mode == "simulate":
        run_simulate(settings)
    else:
        run_ingest(settings)


if __name__ == "__main__":
    main()
