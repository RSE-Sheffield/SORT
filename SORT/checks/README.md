# Django system checks

See: [System check framework](https://docs.djangoproject.com/en/5.2/topics/checks/) in the Django documentation.

To activate a system check, import it to `SORT/checks/__init__.py` and append the function name to the `__all__` list.
This will ensure the check is registered when the application is initialised.
