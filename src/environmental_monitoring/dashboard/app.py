"""Dash application factory.

The dashboard depends only on the `ReadingRepository` port and renders
whatever has actually been ingested and persisted — it never fabricates data
itself. Presentation logic (`_build_figure`, `_build_summary`) is split into
plain functions so it can be unit tested without spinning up Dash's callback
machinery.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objs as go
from dash import Dash, Input, Output, dcc, html

from environmental_monitoring.application.ports import ReadingRepository
from environmental_monitoring.domain.models import AirQualityLevel, SensorReading

REFRESH_INTERVAL_MS = 5_000
DEFAULT_READING_LIMIT = 200

_ASSETS_DIR = Path(__file__).resolve().parent / "assets"

_SERIES_COLOR_PM2_5 = "#2a78d6"
_SERIES_COLOR_PM10 = "#eb6834"
_GRIDLINE_COLOR = "#e1e0d9"
_AXIS_COLOR = "#c3c2b7"
_MUTED_TEXT = "#898781"

# (background, text, label) per AirQualityLevel. Six domain levels fold into
# four status tiers (good/warning/serious/critical) since that's the fixed,
# reserved status palette; severity stays monotonic across the fold.
_STATUS_STYLE: dict[AirQualityLevel, tuple[str, str, str]] = {
    AirQualityLevel.GOOD: ("#0ca30c", "#ffffff", "Good"),
    AirQualityLevel.MODERATE: ("#fab219", "#0b0b0b", "Moderate"),
    AirQualityLevel.UNHEALTHY_FOR_SENSITIVE_GROUPS: (
        "#ec835a",
        "#0b0b0b",
        "Unhealthy (sensitive groups)",
    ),
    AirQualityLevel.UNHEALTHY: ("#d03b3b", "#ffffff", "Unhealthy"),
    AirQualityLevel.VERY_UNHEALTHY: ("#d03b3b", "#ffffff", "Very unhealthy"),
    AirQualityLevel.HAZARDOUS: ("#d03b3b", "#ffffff", "Hazardous"),
}


def _build_figure(readings: list[SensorReading]) -> go.Figure:
    df = pd.DataFrame([r.to_dict() for r in readings])
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    return go.Figure(
        data=[
            go.Scatter(
                x=df["timestamp"],
                y=df["pm2_5"],
                mode="lines",
                name="PM2.5 (µg/m³)",
                line={"color": _SERIES_COLOR_PM2_5, "width": 2},
            ),
            go.Scatter(
                x=df["timestamp"],
                y=df["pm10"],
                mode="lines",
                name="PM10 (µg/m³)",
                line={"color": _SERIES_COLOR_PM10, "width": 2},
            ),
        ],
        layout=go.Layout(
            margin={"l": 48, "r": 16, "t": 16, "b": 40},
            height=340,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={
                "family": "system-ui, -apple-system, Segoe UI, sans-serif",
                "color": _MUTED_TEXT,
            },
            xaxis={"gridcolor": _GRIDLINE_COLOR, "linecolor": _AXIS_COLOR, "showline": True},
            yaxis={
                "title": "Concentration (µg/m³)",
                "gridcolor": _GRIDLINE_COLOR,
                "linecolor": _AXIS_COLOR,
                "showline": True,
                "rangemode": "tozero",
            },
            legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "left", "x": 0},
            hovermode="x unified",
        ),
    )


def _stat_tile(label: str, value: str, accent_class: str = "") -> html.Div:
    return html.Div(
        [
            html.Div(label, className="envmon-stat-label"),
            html.Div(value, className=f"envmon-stat-value {accent_class}".strip()),
        ],
        className="envmon-stat-tile",
    )


def _build_summary(readings: list[SensorReading]) -> list[Any]:
    if not readings:
        return [
            html.Div(
                "Waiting for sensor data — start the simulator or ingestion service.",
                className="envmon-empty",
            )
        ]

    latest = readings[-1]
    sensor_count = len({r.sensor_id for r in readings})
    bg_color, text_color, status_label = _STATUS_STYLE[latest.air_quality_level]

    stat_row = html.Div(
        [
            _stat_tile("PM2.5", f"{latest.pm2_5:.1f} µg/m³", "envmon-stat-accent-pm25"),
            _stat_tile("PM10", f"{latest.pm10:.1f} µg/m³", "envmon-stat-accent-pm10"),
            _stat_tile(
                "Temperature",
                f"{latest.temperature_celsius:.1f} °C"
                if latest.temperature_celsius is not None
                else "—",
            ),
            _stat_tile(
                "Humidity",
                f"{latest.humidity_percent:.1f}%" if latest.humidity_percent is not None else "—",
            ),
        ],
        className="envmon-stat-row",
    )

    status_row = html.Div(
        [
            html.Span(
                status_label,
                className="envmon-status-pill",
                style={"backgroundColor": bg_color, "color": text_color},
            ),
            html.Span(
                f"{len(readings)} readings from {sensor_count} sensor(s) · "
                f"last updated {latest.timestamp.strftime('%H:%M:%S UTC')}"
            ),
        ],
        className="envmon-status-row",
    )

    return [stat_row, status_row]


def create_app(repository: ReadingRepository, *, location: str = "") -> Dash:
    app = Dash(__name__, assets_folder=str(_ASSETS_DIR))
    app.title = "Environmental Monitoring"

    header_children: list[Any] = [
        html.Div(
            [
                html.H1("Air Quality Dashboard", className="envmon-title"),
                html.P(
                    "Live PM2.5 / PM10 readings ingested from the MQTT pipeline.",
                    className="envmon-subtitle",
                ),
            ]
        )
    ]
    if location:
        header_children.append(html.Div(f"📍 {location}", className="envmon-location"))

    app.layout = html.Div(
        [
            html.Div(header_children, className="envmon-header"),
            html.Div(id="summary"),
            html.Div(
                dcc.Graph(id="air-quality-graph", config={"displayModeBar": False}),
                className="envmon-chart-card",
            ),
            html.Div(
                "Data source: SimulatedSensor (synthetic) unless --mode openweather is used for "
                "real measured air-quality data. See docs/ARCHITECTURE.md.",
                className="envmon-footer",
            ),
            dcc.Interval(id="refresh-interval", interval=REFRESH_INTERVAL_MS, n_intervals=0),
        ],
        className="envmon-page",
    )

    @app.callback(
        Output("air-quality-graph", "figure"),
        Output("summary", "children"),
        Input("refresh-interval", "n_intervals"),
    )
    def _refresh(_n_intervals: int) -> tuple[go.Figure, list[Any]]:
        readings = repository.latest(DEFAULT_READING_LIMIT)
        figure = _build_figure(readings) if readings else go.Figure()
        return figure, _build_summary(readings)

    return app
