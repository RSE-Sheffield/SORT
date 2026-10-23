import itertools
from pathlib import Path

import django.contrib.staticfiles.finders
from django.conf import settings
from django.core.checks import Error, Tags

FILENAMES = itertools.chain(
    settings.SURVEY_TEMPLATES.values(), settings.DEMOGRAPHY_TEMPLATES.values(), (settings.CONSENT_TEMPLATE,)
)


@django.core.checks.register(Tags.staticfiles)
def check_survey_config(*args, **kwargs) -> list[Error]:
    """
    Ensure that survey configuration files exist
    """
    errors = list()

    # Iterate over survey config files
    for filename in FILENAMES:
        path = Path(settings.SURVEY_TEMPLATE_DIR).joinpath(filename).absolute()
        if not path.exists():
            errors.append(Error(f"File not found: {path}", hint="Make sure the survey config file is present."))

    return errors
