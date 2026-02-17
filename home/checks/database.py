"""
Database connection system checks.

These checks verify database connectivity during deployment and development.
Run with: python manage.py check
"""

from django.core.checks import Error, register, Tags
from django.db import connection
from django.db.utils import OperationalError


@register(Tags.database)
def check_database_connection(app_configs, **kwargs):
    """
    Verify that the database connection is working.

    This check attempts to connect to the database and execute a simple query.
    It's particularly important during deployment to catch configuration issues
    early before the application starts serving requests.

    Registered with Tags.database so it runs with `manage.py check --database`.
    """

    errors = list()

    try:
        # Close any existing connection to force a fresh connection attempt
        connection.close()

        # Attempt to connect and execute a simple query
        # This will raise OperationalError if connection fails
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

            if result != (1,):
                errors.append(
                    Error(
                        "Database connection succeeded but query returned unexpected result.",
                        hint="Check database configuration and permissions.",
                        id="home.E001",
                    )
                )
    except OperationalError as e:
        errors.append(
            Error(
                f"Cannot connect to database: {e}",
                hint=(
                    "Check DJANGO_DATABASE_* environment variables, "
                    "ensure PostgreSQL is running, and verify credentials."
                ),
                id="home.E002",
            )
        )
    except Exception as e:
        errors.append(
            Error(
                f"Unexpected error testing database connection: {e}",
                hint="Check database configuration in settings.py",
                id="home.E003",
            )
        )

    return errors
