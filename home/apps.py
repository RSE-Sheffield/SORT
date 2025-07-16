from django.apps import AppConfig


class HomeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "home"

    def ready(self):
        """
        Initialise this app
        """
        # Load system checks
        # https://docs.djangoproject.com/en/5.2/topics/checks/
        # Suppress linting errors
        import home.checks  # noqa: F401
        import survey.checks  # noqa: F401
