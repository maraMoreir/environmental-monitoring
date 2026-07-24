# 2. SQLite for demo persistence

## Status

Accepted

## Context

The ingestion service needs somewhere durable to put validated readings so
the dashboard can render real history instead of an in-memory buffer that
resets on every restart. The project intentionally runs with zero paid
cloud resources by default (see ADR 0003 on AWS IoT being optional).

## Decision

`SqliteReadingRepository` implements `ReadingRepository` with the stdlib
`sqlite3` module: one file, WAL journal mode for concurrent
reader/writer access (the dashboard reads while ingestion writes), a real
schema with an index on `timestamp`, and parameterized queries throughout
(see `tests/infrastructure/test_repository.py::test_sensor_id_with_sql_metacharacters_is_stored_safely`
for a concrete injection-safety regression test).

## Consequences

- Zero extra infrastructure: no database server/container, no credentials
  to manage.
- A real relational store, not a CSV - proper types, an index, and
  transactional writes, so the pattern generalizes to a managed database
  without a rewrite (only `repository.py` would change).
- SQLite's single-writer model is a genuine limitation at production scale;
  it is appropriate here because the demo has exactly one ingestion writer.
  A production deployment would swap this adapter for Postgres/Timestream
  behind the same `ReadingRepository` port.
