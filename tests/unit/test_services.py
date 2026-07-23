from __future__ import annotations

import logging

import pytest

from environmental_monitoring.application.services import IngestionService
from environmental_monitoring.domain.models import SensorReading


class FakeRepository:
    def __init__(self) -> None:
        self.saved: list[SensorReading] = []

    def save(self, reading: SensorReading) -> None:
        self.saved.append(reading)

    def latest(self, limit: int = 100) -> list[SensorReading]:
        return self.saved[-limit:]


class FakePublisher:
    def __init__(self, *, fail: bool = False) -> None:
        self.published: list[SensorReading] = []
        self._fail = fail

    def publish(self, reading: SensorReading) -> None:
        if self._fail:
            raise RuntimeError("cloud is down")
        self.published.append(reading)


def test_ingest_persists_reading(valid_reading: SensorReading) -> None:
    repository = FakeRepository()
    service = IngestionService(repository)

    service.ingest(valid_reading)

    assert repository.saved == [valid_reading]


def test_ingest_forwards_to_cloud_publisher_when_configured(valid_reading: SensorReading) -> None:
    repository = FakeRepository()
    publisher = FakePublisher()
    service = IngestionService(repository, cloud_publisher=publisher)

    service.ingest(valid_reading)

    assert publisher.published == [valid_reading]


def test_ingest_survives_cloud_publisher_failure(
    valid_reading: SensorReading, caplog: pytest.LogCaptureFixture
) -> None:
    repository = FakeRepository()
    publisher = FakePublisher(fail=True)
    service = IngestionService(repository, cloud_publisher=publisher)

    with caplog.at_level(logging.ERROR):
        service.ingest(valid_reading)  # must not raise

    assert repository.saved == [valid_reading]
    assert "Cloud forwarding failed" in caplog.text
