"""FastAPI application factory.

Like the dashboard, this depends only on the `ReadingRepository` port —
it's a second, independent way to consume the same persisted data (e.g. for
another service or a mobile client), not a second data pipeline.
"""

from __future__ import annotations

from fastapi import FastAPI, Query

from environmental_monitoring.api.schemas import ReadingResponse
from environmental_monitoring.application.ports import ReadingRepository

DEFAULT_READING_LIMIT = 100
MAX_READING_LIMIT = 1000


def create_app(repository: ReadingRepository) -> FastAPI:
    app = FastAPI(
        title="Environmental Monitoring API",
        description="Read-only REST API over ingested sensor readings.",
        version="1.0.0",
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readings/latest", response_model=list[ReadingResponse])
    def latest_readings(
        limit: int = Query(
            default=DEFAULT_READING_LIMIT,
            ge=1,
            le=MAX_READING_LIMIT,
            description="Maximum number of readings to return, most recent last.",
        ),
    ) -> list[ReadingResponse]:
        return [ReadingResponse.from_domain(reading) for reading in repository.latest(limit)]

    return app
