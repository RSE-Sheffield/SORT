from pathlib import Path
import django.core.checks
import django.conf
import django.contrib.staticfiles.finders

settings = django.conf.settings


@django.core.checks.register(django.core.checks.Tags.staticfiles)
def check_manifest(*args, **kwargs) -> list[django.core.checks.Error]:
    """
    Ensure that the Vite manifest file is present.
    https://vite.dev/guide/backend-integration

    This is a Django system check:
    https://docs.djangoproject.com/en/5.2/topics/checks/
    """
    errors = list()

    # Check the settings is specified
    if not getattr(settings, 'VITE_MANIFEST_FILE_PATH', None):
        errors.append(
            django.core.checks.Error(
                "Setting not defined VITE_MANIFEST_FILE_PATH",
                hint="Add VITE_MANIFEST_FILE_PATH to settings.py",
                id="SORT.E001",
            ),
        )

    # Find the manifest.json file in the static folder
    path = django.contrib.staticfiles.finders.find(settings.VITE_MANIFEST_FILE_PATH)

    # Check if manifest.json is present
    if not path:
        absolute_path = Path(settings.STATIC_ROOT).joinpath(settings.VITE_MANIFEST_FILE_PATH).absolute()
        errors.append(
            django.core.checks.Error(
                f"File not found: '{absolute_path}'",
                hint="Ensure that the JavaScript project has been built (npm run build)",
                id="SORT.E002",
            ),
        )

    return errors
