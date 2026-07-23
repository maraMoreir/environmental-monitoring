# 1. Hexagonal architecture (ports & adapters)

## Status

Accepted

## Context

The original codebase was four unconnected scripts: an MQTT sensor loop, an
AWS IoT publisher with embedded credential placeholders, a dashboard that
plotted `random.uniform()` instead of any real data, and a config module.
Nothing was composable, nothing was testable without a live broker or a live
AWS account, and the "pipeline" wasn't actually wired together — hence the
README instructing users to run a `monitoring.py` that didn't exist.

## Decision

Split the codebase into four layers, each depending only inward:

- `domain/` — `SensorReading`, `AirQualityLevel`, validation. No I/O, no
  framework imports.
- `application/` — `ports.py` defines `Protocol` interfaces
  (`ReadingSource`, `ReadingPublisher`, `ReadingSubscriber`,
  `ReadingRepository`); `services.py` (`IngestionService`) orchestrates
  against those interfaces only.
- `infrastructure/` — concrete adapters: `mqtt_broker.py` (paho-mqtt),
  `aws_iot.py` (boto3), `repository.py` (SQLite), `simulator.py` (synthetic
  data source).
- `dashboard/` — a Dash app that depends on the `ReadingRepository` port,
  not on how data got there.

`cli.py` is the only place that wires concrete adapters into the
application layer (composition root).

## Consequences

- `IngestionService` is tested with in-memory fakes — no broker, no
  database, no network in unit tests (`tests/unit/test_services.py`).
- Swapping SQLite for Postgres, or paho-mqtt for a different client, means
  writing one new adapter class; nothing in `domain/` or `application/`
  changes.
- The dashboard cannot regress into plotting fake data by construction: it
  has no code path that generates readings itself.
- Slightly more files/indirection than a single script — a deliberate
  trade for testability and swappability, appropriate once a pipeline has
  more than one moving part.
