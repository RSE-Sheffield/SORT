from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
from .layouts import create_dashboard_layout
from .callbacks import register_callbacks


dash_app = DjangoDash(
    "SurveyDashboard",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    external_scripts=[
        "https://cdn.plot.ly/plotly-2.20.0.min.js"
    ],  # This line is needed for graphs
)

dash_app.layout = create_dashboard_layout()

register_callbacks(dash_app)
