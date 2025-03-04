"""
Django settings for SORT project.

Generated by 'django-admin startproject' using Django 5.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def cast_to_boolean(obj: Any) -> bool:
    """
    Check if the string value is 1, yes, or true.

    Empty values are interpreted as False.
    """
    # Cast to lower case string
    obj = str(obj).casefold()
    # False / off
    if obj in {"", "off", "none"}:
        return False
    # True / on
    return obj[0] in {"1", "y", "t", "o"}


# Load environment variables from .env file
load_dotenv(os.getenv("DJANGO_ENV_PATH"))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Path when redirecting to login
LOGIN_URL = "/login/"

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = cast_to_boolean(os.getenv("DJANGO_DEBUG", "False"))

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "sort-web-app.shef.ac.uk").split()

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_bootstrap5",
    "django_extensions",
    "debug_toolbar",
    "qr_code",
    # apps created by FA:
    "home",
    "survey",
]

MIDDLEWARE = [
    # Implement security in the web server, not in Django.
    # https://docs.djangoproject.com/en/5.1/ref/middleware/#module-django.middleware.security
    # "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

ROOT_URLCONF = "SORT.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "static/templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = os.getenv("DJANGO_WSGI_APPLICATION", "SORT.wsgi.application")

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
DATABASES = {
    # Set the database settings using environment variables, or default to a local SQLite database file.
    "default": {
        "ENGINE": os.getenv("DJANGO_DATABASE_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DJANGO_DATABASE_NAME", BASE_DIR / "db.sqlite3"),
        "USER": os.getenv("DJANGO_DATABASE_USER"),
        "PASSWORD": os.getenv("DJANGO_DATABASE_PASSWORD"),
        "HOST": os.getenv("DJANGO_DATABASE_HOST"),
        "PORT": os.getenv("DJANGO_DATABASE_PORT"),
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-gb"

TIME_ZONE = "Europe/London"

# Disable translation features
USE_I18N = False

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "static/"

STATICFILES_DIRS = [BASE_DIR / "static"]

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# FA: End session when the browser is closed
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# FA: 30 minutes before automatic log out
SESSION_COOKIE_AGE = 1800

PASSWORD_RESET_TIMEOUT = 1800  # FA: default to expire after 30 minutes

# FA: for local testing emails:

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)

# For django-debug-toolbar
INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    # ...
]
AUTH_USER_MODEL = 'home.User'  # FA: replace username with email as unique identifiers

# FA: for production:

# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

STATIC_ROOT = os.getenv("DJANGO_STATIC_ROOT")

# Security settings
SESSION_COOKIE_SECURE = cast_to_boolean(
    os.getenv("DJANGO_SESSION_COOKIE_SECURE", not DEBUG)
)
CSRF_COOKIE_SECURE = cast_to_boolean(os.getenv("DJANGO_CSRF_COOKIE_SECURE", not DEBUG))

# Logging
# https://docs.djangoproject.com/en/5.1/topics/logging/
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    # Send log messages to the standard output, which will be sent to the Gunicorn service logs
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("DJANGO_LOG_LEVEL", "WARNING"),
    },
}
