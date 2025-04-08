from django.apps import AppConfig


class DashboardsConfig(AppConfig):
    """
    Configuration class for the survey dashboards application.

    This class defines application-specific configurations, including the
    default auto field and the application name, which is used in settings.py.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "survey.dashboards"
