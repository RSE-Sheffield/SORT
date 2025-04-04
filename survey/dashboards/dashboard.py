"""
Factory module for the survey dashboard.

This module initialises and configures the Plotly Dash applications.
It connects the dashboard to survey data sources, prepares section and demographic configurations, and
registers the necessary callbacks for interactive functionality.
"""

from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
from dash import html
from .layouts import create_dashboard_layout
from .callbacks import register_callbacks
from survey.models import SurveyResponse, Survey
from .config import get_sections_from_survey, get_demographic_fields_from_survey


def get_survey_dashboard(survey_id):
    """
    Gets or creates a dashboard for a specified survey
    """
    app_name = f"SurveyDashboard_{survey_id}"

    # Create the Dash app
    dash_app = DjangoDash(
        app_name,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        external_scripts=["https://cdn.plot.ly/plotly-2.20.0.min.js"], # This URL is needed to display charts correctly
        serve_locally=False # Loads assets from CDN  (Content Delivery Network) instead of locally
    )

    # Get the survey and its responses
    try:
        survey = Survey.objects.get(id=survey_id)
        survey_responses = list(SurveyResponse.objects.filter(survey=survey).values())
        dash_app.survey = survey
        dash_app.survey_responses = survey_responses
        dash_app.sections = get_sections_from_survey(survey)
        dash_app.demographic_fields = get_demographic_fields_from_survey(survey)

        dash_app.layout = create_dashboard_layout(dash_app)

        register_callbacks(dash_app)

        return dash_app

    except Exception as e:
        print(f"Error creating dashboard: {e}")
        dash_app.layout = html.Div([
            html.H3("Error creating dashboard"),
            html.P(str(e))
        ])
        return dash_app
