"""Run with: python -m environmental_monitoring.api"""

from __future__ import annotations

import logging

import uvicorn

from environmental_monitoring.api.app import create_app
from environmental_monitoring.config import get_settings
from environmental_monitoring.infrastructure.repository import SqliteReadingRepository


def main() -> None:
    logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = get_settings()
    repository = SqliteReadingRepository(settings.database_path)
    app = create_app(repository)
    uvicorn.run(app, host="0.0.0.0", port=settings.api_port)  # noqa: S104


if __name__ == "__main__":
    main()
