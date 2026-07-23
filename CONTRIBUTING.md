# Contributing

## Setup

```bash
python -m venv env
source env/bin/activate  # Windows: .\env\Scripts\activate
pip install -e ".[dev]"
```

## Before opening a PR

```bash
ruff format .
ruff check .
mypy src
pytest
```

All four must pass — this is exactly what CI (`.github/workflows/ci.yml`)
runs on every push and pull request, across Python 3.11–3.13.

## Architecture

Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and the ADRs in
[docs/adr/](docs/adr/) before making structural changes. In short: `domain/`
has no I/O, `application/` depends only on the `Protocol`s in `ports.py`,
and concrete implementations live in `infrastructure/`. If you're adding a
new data store or transport, it should be a new adapter implementing an
existing port, not a change to `application/services.py`.

## Tests

New behavior needs a test. Unit tests for `domain`/`application` use
in-memory fakes (see `tests/unit/test_services.py`); adapter tests mock the
underlying client (paho-mqtt, boto3) or use a `tmp_path` SQLite file — none
of the test suite touches a live broker, database server, or AWS account.
