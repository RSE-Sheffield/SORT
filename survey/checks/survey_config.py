from pathlib import Path
from django.core.checks import Tags, Error
import django.conf
import django.contrib.staticfiles.finders

settings = django.conf.settings

SURVEY_CONFIG_FILE_PATHS = {
    "data/survey_config/consent_only_config.json",
    "data/survey_config/demography_only_config.json"
}


@django.core.checks.register(Tags.staticfiles)
def check_survey_config(*args, **kwargs) -> list[Error]:
    """
    Ensure that survey configuration files exist
    """
    errors = list()

    for path in SURVEY_CONFIG_FILE_PATHS:
        path = Path(path).absolute()
        if not path.exists():
            errors.append(
                Error(f"File not found: {path}", hint="Make sure the survey config file is present.")
            )

    return errors
