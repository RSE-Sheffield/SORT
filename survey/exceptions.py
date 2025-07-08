from django.core.exceptions import ValidationError


class SurveyInactiveError(ValidationError):
    """
    A survey is paused so no data is being gathered.
    """

    pass
