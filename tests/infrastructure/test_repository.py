from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from environmental_monitoring.domain.models import SensorReading
from environmental_monitoring.infrastructure.repository import SqliteReadingRepository


def _reading(sensor_id: str, minute: int) -> SensorReading:
    return SensorReading(
        sensor_id=sensor_id,
        timestamp=datetime(2026, 1, 1, 12, minute, tzinfo=UTC),
        pm2_5=10.0 + minute,
        pm10=20.0 + minute,
    )


def test_save_and_latest_roundtrip(tmp_path: Path) -> None:
    repo = SqliteReadingRepository(tmp_path / "readings.db")
    reading = _reading("sensor-001", 0)

    repo.save(reading)

    assert repo.latest() == [reading]


def test_latest_returns_chronological_order(tmp_path: Path) -> None:
    repo = SqliteReadingRepository(tmp_path / "readings.db")
    readings = [_reading("sensor-001", m) for m in range(5)]
    for reading in readings:
        repo.save(reading)

    assert repo.latest() == readings


def test_latest_respects_limit(tmp_path: Path) -> None:
    repo = SqliteReadingRepository(tmp_path / "readings.db")
    for m in range(5):
        repo.save(_reading("sensor-001", m))

    result = repo.latest(limit=2)

    assert result == [_reading("sensor-001", 3), _reading("sensor-001", 4)]


def test_creates_parent_directory_if_missing(tmp_path: Path) -> None:
    db_path = tmp_path / "nested" / "readings.db"

    SqliteReadingRepository(db_path)

    assert db_path.parent.is_dir()


def test_reopening_existing_database_preserves_data(tmp_path: Path) -> None:
    db_path = tmp_path / "readings.db"
    SqliteReadingRepository(db_path).save(_reading("sensor-001", 0))

    reopened = SqliteReadingRepository(db_path)

    assert reopened.latest() == [_reading("sensor-001", 0)]


def test_sensor_id_with_sql_metacharacters_is_stored_safely(tmp_path: Path) -> None:
    repo = SqliteReadingRepository(tmp_path / "readings.db")
    malicious_id = "sensor'; DROP TABLE readings;--"
    reading = SensorReading(
        sensor_id=malicious_id, timestamp=datetime(2026, 1, 1, tzinfo=UTC), pm2_5=1.0, pm10=2.0
    )

    repo.save(reading)

    assert [r.sensor_id for r in repo.latest()] == [malicious_id]


def test_latest_filters_by_sensor_id(tmp_path: Path) -> None:
    repo = SqliteReadingRepository(tmp_path / "readings.db")
    repo.save(_reading("br-sp", 0))
    repo.save(_reading("br-rj", 1))
    repo.save(_reading("br-sp", 2))

    result = repo.latest(sensor_id="br-rj")

    assert result == [_reading("br-rj", 1)]


def test_distinct_sensor_ids_returns_sorted_unique_ids(tmp_path: Path) -> None:
    repo = SqliteReadingRepository(tmp_path / "readings.db")
    repo.save(_reading("br-sp", 0))
    repo.save(_reading("br-rj", 1))
    repo.save(_reading("br-sp", 2))

    assert repo.distinct_sensor_ids() == ["br-rj", "br-sp"]


def test_distinct_sensor_ids_empty_when_no_readings(tmp_path: Path) -> None:
    repo = SqliteReadingRepository(tmp_path / "readings.db")

    assert repo.distinct_sensor_ids() == []
