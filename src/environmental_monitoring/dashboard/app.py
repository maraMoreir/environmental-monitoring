"""Dash application factory.

The dashboard depends only on the `ReadingRepository` port and renders
whatever has actually been ingested and persisted — it never fabricates data
itself. Presentation logic (`_build_figure`, `_build_summary`,
`_build_sensor_options`) is split into plain functions so it can be unit
tested without spinning up Dash's callback machinery.

User-facing copy is in Portuguese (the product is a Brazilian air-quality
dashboard); identifiers, comments, and docstrings stay in English like the
rest of the codebase.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objs as go
from dash import Dash, Input, Output, State, dcc, html

from environmental_monitoring.application.ports import ReadingRepository
from environmental_monitoring.domain.locations import BRAZIL_STATE_CAPITALS
from environmental_monitoring.domain.models import AirQualityLevel, SensorReading

REFRESH_INTERVAL_MS = 5_000
DEFAULT_READING_LIMIT = 200

_ASSETS_DIR = Path(__file__).resolve().parent / "assets"

_SERIES_COLOR_PM2_5 = "#2a78d6"
_SERIES_COLOR_PM10 = "#eb6834"
_GRIDLINE_COLOR = "#e1e0d9"
_AXIS_COLOR = "#c3c2b7"
_MUTED_TEXT = "#898781"

_BRAZIL_SENSOR_LABELS: dict[str, str] = {loc.sensor_id: loc.label for loc in BRAZIL_STATE_CAPITALS}

# (background, text, label) per AirQualityLevel. Six domain levels fold into
# four status tiers (good/warning/serious/critical) since that's the fixed,
# reserved status palette; severity stays monotonic across the fold.
_STATUS_STYLE: dict[AirQualityLevel, tuple[str, str, str]] = {
    AirQualityLevel.GOOD: ("#0ca30c", "#ffffff", "Boa"),
    AirQualityLevel.MODERATE: ("#fab219", "#0b0b0b", "Moderada"),
    AirQualityLevel.UNHEALTHY_FOR_SENSITIVE_GROUPS: (
        "#ec835a",
        "#0b0b0b",
        "Insalubre (grupos sensíveis)",
    ),
    AirQualityLevel.UNHEALTHY: ("#d03b3b", "#ffffff", "Insalubre"),
    AirQualityLevel.VERY_UNHEALTHY: ("#d03b3b", "#ffffff", "Muito insalubre"),
    AirQualityLevel.HAZARDOUS: ("#d03b3b", "#ffffff", "Perigosa"),
}


def _sensor_label(sensor_id: str, *, default_sensor_id: str = "", default_label: str = "") -> str:
    if sensor_id in _BRAZIL_SENSOR_LABELS:
        return _BRAZIL_SENSOR_LABELS[sensor_id]
    if sensor_id == default_sensor_id and default_label:
        return default_label
    return sensor_id


def _build_sensor_options(
    sensor_ids: list[str], *, default_sensor_id: str = "", default_label: str = ""
) -> list[dict[str, str]]:
    return [
        {
            "label": _sensor_label(
                sid, default_sensor_id=default_sensor_id, default_label=default_label
            ),
            "value": sid,
        }
        for sid in sensor_ids
    ]


def _resolve_sensor_selection(
    sensor_ids: list[str], current_value: str | None, default_sensor_id: str = ""
) -> str | None:
    """Keep the current dropdown selection if it's still valid; otherwise fall
    back to the configured default sensor, or the first sensor available."""
    if current_value in sensor_ids:
        return current_value
    if default_sensor_id in sensor_ids:
        return default_sensor_id
    return sensor_ids[0] if sensor_ids else None


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
                "title": "Concentração (µg/m³)",
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


def _build_summary(
    readings: list[SensorReading], *, default_sensor_id: str = "", default_label: str = ""
) -> list[Any]:
    if not readings:
        return [
            html.Div(
                "Aguardando dados do sensor — inicie o simulador ou o serviço de ingestão.",
                className="envmon-empty",
            )
        ]

    latest = readings[-1]
    location_label = _sensor_label(
        latest.sensor_id, default_sensor_id=default_sensor_id, default_label=default_label
    )
    bg_color, text_color, status_label = _STATUS_STYLE[latest.air_quality_level]

    stat_row = html.Div(
        [
            _stat_tile("PM2.5", f"{latest.pm2_5:.1f} µg/m³", "envmon-stat-accent-pm25"),
            _stat_tile("PM10", f"{latest.pm10:.1f} µg/m³", "envmon-stat-accent-pm10"),
            _stat_tile(
                "Temperatura",
                f"{latest.temperature_celsius:.1f} °C"
                if latest.temperature_celsius is not None
                else "—",
            ),
            _stat_tile(
                "Umidade",
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
                f"{len(readings)} leituras — {location_label} · "
                f"atualizado às {latest.timestamp.strftime('%H:%M:%S UTC')}"
            ),
        ],
        className="envmon-status-row",
    )

    return [stat_row, status_row]


def create_app(
    repository: ReadingRepository, *, default_sensor_id: str = "", default_sensor_label: str = ""
) -> Dash:
    app = Dash(__name__, assets_folder=str(_ASSETS_DIR))
    app.title = "Monitoramento Ambiental"

    # Dropdown starts empty; the options/refresh callback below populates it
    # on first load and keeps it in sync with whichever sensors have
    # actually published, on every refresh tick — a sensor that starts
    # publishing after the dashboard is already running still shows up
    # within one refresh interval, no restart needed.
    app.layout = html.Div(
        [
            html.Div(
                [
                    html.H1("Painel de Qualidade do Ar", className="envmon-title"),
                    html.P(
                        "Leituras de PM2.5 / PM10 em tempo real, ingeridas via pipeline MQTT.",
                        className="envmon-subtitle",
                    ),
                ],
                className="envmon-header",
            ),
            html.Div(
                [
                    html.Label(
                        "Estado / sensor", htmlFor="sensor-select", className="envmon-stat-label"
                    ),
                    dcc.Dropdown(
                        id="sensor-select",
                        options=[],
                        value=None,
                        clearable=False,
                        placeholder="Selecione um estado...",
                    ),
                ],
                className="envmon-select-row",
            ),
            html.Div(id="summary"),
            html.Div(
                dcc.Graph(id="air-quality-graph", config={"displayModeBar": False}),
                className="envmon-chart-card",
            ),
            html.Div(
                "As leituras são ingeridas via MQTT a partir da fonte configurada no pipeline "
                "— dados reais da OpenWeatherMap ou o simulador sintético. Veja "
                "docs/ARCHITECTURE.md.",
                className="envmon-footer",
            ),
            dcc.Interval(id="refresh-interval", interval=REFRESH_INTERVAL_MS, n_intervals=0),
        ],
        className="envmon-page",
    )

    @app.callback(
        Output("sensor-select", "options"),
        Output("sensor-select", "value"),
        Input("refresh-interval", "n_intervals"),
        State("sensor-select", "value"),
    )
    def _refresh_sensor_options(
        _n_intervals: int, current_value: str | None
    ) -> tuple[list[dict[str, str]], str | None]:
        sensor_ids = repository.distinct_sensor_ids()
        options = _build_sensor_options(
            sensor_ids, default_sensor_id=default_sensor_id, default_label=default_sensor_label
        )
        selected = _resolve_sensor_selection(sensor_ids, current_value, default_sensor_id)
        return options, selected

    @app.callback(
        Output("air-quality-graph", "figure"),
        Output("summary", "children"),
        Input("refresh-interval", "n_intervals"),
        Input("sensor-select", "value"),
    )
    def _refresh_readings(
        _n_intervals: int, selected_sensor_id: str | None
    ) -> tuple[go.Figure, list[Any]]:
        readings = repository.latest(DEFAULT_READING_LIMIT, sensor_id=selected_sensor_id)
        figure = _build_figure(readings) if readings else go.Figure()
        summary = _build_summary(
            readings, default_sensor_id=default_sensor_id, default_label=default_sensor_label
        )
        return figure, summary

    return app
