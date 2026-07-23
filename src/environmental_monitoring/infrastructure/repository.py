"""SQLite-backed ReadingRepository.

SQLite was chosen for the demo because it's zero-infrastructure (a single
file, no server process) while still exercising a real relational store with
a proper schema, an index, and parameterized queries. See
docs/adr/0002-sqlite-demo-persistence.md.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from environmental_monitoring.domain.models import SensorReading

_SCHEMA = """
CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    pm2_5 REAL NOT NULL,
    pm10 REAL NOT NULL,
    temperature_celsius REAL,
    humidity_percent REAL
);
CREATE INDEX IF NOT EXISTS idx_readings_timestamp ON readings (timestamp);
"""

_INSERT = """
INSERT INTO readings (sensor_id, timestamp, pm2_5, pm10, temperature_celsius, humidity_percent)
VALUES (?, ?, ?, ?, ?, ?)
"""

_SELECT_LATEST_ALL = """
SELECT sensor_id, timestamp, pm2_5, pm10, temperature_celsius, humidity_percent
FROM readings
ORDER BY timestamp DESC
LIMIT ?
"""

_SELECT_LATEST_BY_SENSOR = """
SELECT sensor_id, timestamp, pm2_5, pm10, temperature_celsius, humidity_percent
FROM readings
WHERE sensor_id = ?
ORDER BY timestamp DESC
LIMIT ?
"""

_SELECT_DISTINCT_SENSOR_IDS = "SELECT DISTINCT sensor_id FROM readings ORDER BY sensor_id"


class SqliteReadingRepository:
    """`ReadingRepository` implementation backed by a local SQLite file."""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn, conn:
            conn.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def save(self, reading: SensorReading) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                _INSERT,
                (
                    reading.sensor_id,
                    reading.timestamp.isoformat(),
                    reading.pm2_5,
                    reading.pm10,
                    reading.temperature_celsius,
                    reading.humidity_percent,
                ),
            )

    def latest(self, limit: int = 100, *, sensor_id: str | None = None) -> list[SensorReading]:
        with closing(self._connect()) as conn:
            if sensor_id is None:
                rows = conn.execute(_SELECT_LATEST_ALL, (limit,)).fetchall()
            else:
                rows = conn.execute(_SELECT_LATEST_BY_SENSOR, (sensor_id, limit)).fetchall()
        readings = [
            SensorReading(
                sensor_id=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                pm2_5=row[2],
                pm10=row[3],
                temperature_celsius=row[4],
                humidity_percent=row[5],
            )
            for row in rows
        ]
        readings.reverse()  # rows come back newest-first; charts want chronological order
        return readings

    def distinct_sensor_ids(self) -> list[str]:
        with closing(self._connect()) as conn:
            rows = conn.execute(_SELECT_DISTINCT_SENSOR_IDS).fetchall()
        return [row[0] for row in rows]
