from .survey import SurveyService

# Create instances for use in views
survey_service = SurveyService()

__all__ = [
    "survey_service",
]
