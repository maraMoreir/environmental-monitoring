"""Run with: python -m environmental_monitoring.dashboard"""

from __future__ import annotations

import logging

from environmental_monitoring.config import get_settings
from environmental_monitoring.dashboard.app import create_app
from environmental_monitoring.infrastructure.repository import SqliteReadingRepository


def main() -> None:
    logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = get_settings()
    repository = SqliteReadingRepository(settings.database_path)
    app = create_app(repository, location=settings.sensor_location_label)
    app.run(host="0.0.0.0", port=settings.dashboard_port, debug=settings.debug)  # noqa: S104


if __name__ == "__main__":
    main()
