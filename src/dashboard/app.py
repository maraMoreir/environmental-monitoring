import dash
from dash import dcc, html
import plotly.graph_objs as go
import pandas as pd
import random  

data = {
    "timestamp": pd.date_range(start="2023-07-01", periods=100, freq='H'),
    "pm2.5": [random.uniform(0, 100) for _ in range(100)],
    "pm10": [random.uniform(0, 100) for _ in range(100)]
}

df = pd.DataFrame(data)

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Dashboard de Qualidade do Ar"),
    dcc.Graph(
        id='air-quality-graph',
        figure={
            'data': [
                go.Scatter(
                    x=df['timestamp'],
                    y=df['pm2.5'],
                    mode='lines',
                    name='PM2.5'
                ),
                go.Scatter(
                    x=df['timestamp'],
                    y=df['pm10'],
                    mode='lines',
                    name='PM10'
                )
            ],
            'layout': go.Layout(
                title='Níveis de Qualidade do Ar',
                xaxis={'title': 'Timestamp'},
                yaxis={'title': 'Concentração (µg/m³)'}
            )
        }
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
