"""Use-case orchestration for the ingestion pipeline."""

from __future__ import annotations

import logging

from environmental_monitoring.application.ports import ReadingPublisher, ReadingRepository
from environmental_monitoring.domain.models import SensorReading

logger = logging.getLogger(__name__)


class IngestionService:
    """Persists a validated `SensorReading` and optionally cloud-forwards it.

    Validation itself lives in `SensorReading.__post_init__` (the adapter that
    decodes a wire payload is responsible for constructing one); this service
    depends only on the `ReadingRepository`/`ReadingPublisher` ports, so it has
    no idea whether readings arrived over MQTT, whether they land in SQLite or
    a managed database, or whether the cloud forwarder is AWS IoT Core or a
    test double.
    """

    def __init__(
        self,
        repository: ReadingRepository,
        cloud_publisher: ReadingPublisher | None = None,
    ) -> None:
        self._repository = repository
        self._cloud_publisher = cloud_publisher

    def ingest(self, reading: SensorReading) -> None:
        self._repository.save(reading)
        if self._cloud_publisher is None:
            return
        try:
            # Cloud forwarding is best-effort: a flaky AWS connection must never
            # take down local ingestion, which already succeeded above.
            self._cloud_publisher.publish(reading)
        except Exception:
            logger.exception(
                "Cloud forwarding failed for sensor %s; reading was persisted locally.",
                reading.sensor_id,
            )
