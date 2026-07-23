"""Ports: the interfaces the application core depends on.

Infrastructure adapters implement these `Protocol`s; nothing in `domain/` or
`application/` imports a concrete adapter, which is what lets `IngestionService`
be tested with in-memory fakes instead of a real broker or database.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from environmental_monitoring.domain.models import SensorReading


class ReadingSource(Protocol):
    """Produces sensor readings — real hardware or a simulator."""

    def read(self) -> SensorReading: ...


class ReadingPublisher(Protocol):
    """Publishes a single reading to a message transport (MQTT, AWS IoT, ...)."""

    def publish(self, reading: SensorReading) -> None: ...


class ReadingSubscriber(Protocol):
    """Subscribes to a transport, invoking a callback for each incoming reading."""

    def subscribe(self, on_reading: Callable[[SensorReading], None]) -> None: ...


class ReadingRepository(Protocol):
    """Persists and queries sensor readings."""

    def save(self, reading: SensorReading) -> None: ...

    def latest(self, limit: int = 100, *, sensor_id: str | None = None) -> list[SensorReading]: ...

    def distinct_sensor_ids(self) -> list[str]: ...
