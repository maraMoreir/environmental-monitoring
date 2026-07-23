"""Dash application factory.

The dashboard depends only on the `ReadingRepository` port and renders
whatever has actually been ingested and persisted — it never fabricates data
itself. The figure-building logic is a plain function (`_build_figure_and_status`)
so it can be unit tested without spinning up Dash's callback machinery.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objs as go
from dash import Dash, Input, Output, dcc, html

from environmental_monitoring.application.ports import ReadingRepository
from environmental_monitoring.domain.models import SensorReading

REFRESH_INTERVAL_MS = 5_000
DEFAULT_READING_LIMIT = 200


def _build_figure_and_status(readings: list[SensorReading]) -> tuple[go.Figure, str]:
    if not readings:
        return go.Figure(), "Waiting for sensor data..."

    df = pd.DataFrame([r.to_dict() for r in readings])
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    figure = go.Figure(
        data=[
            go.Scatter(x=df["timestamp"], y=df["pm2_5"], mode="lines", name="PM2.5 (µg/m³)"),
            go.Scatter(x=df["timestamp"], y=df["pm10"], mode="lines", name="PM10 (µg/m³)"),
        ],
        layout=go.Layout(
            title="Particulate Matter Levels",
            xaxis={"title": "Time"},
            yaxis={"title": "Concentration (µg/m³)"},
        ),
    )
    latest = readings[-1]
    status = (
        f"{len(readings)} readings from {df['sensor_id'].nunique()} sensor(s) — "
        f"latest: {latest.air_quality_level.value} (PM2.5={latest.pm2_5} µg/m³)"
    )
    return figure, status


def create_app(repository: ReadingRepository) -> Dash:
    app = Dash(__name__)
    app.title = "Environmental Monitoring"

    app.layout = html.Div(
        [
            html.H1("Air Quality Dashboard"),
            html.P(id="status-line"),
            dcc.Graph(id="air-quality-graph"),
            dcc.Interval(id="refresh-interval", interval=REFRESH_INTERVAL_MS, n_intervals=0),
        ]
    )

    @app.callback(
        Output("air-quality-graph", "figure"),
        Output("status-line", "children"),
        Input("refresh-interval", "n_intervals"),
    )
    def _refresh(_n_intervals: int) -> tuple[go.Figure, str]:
        return _build_figure_and_status(repository.latest(DEFAULT_READING_LIMIT))

    return app
