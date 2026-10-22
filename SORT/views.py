"""Project-level views for the SORT project."""

import logging

from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)


def csrf_failure(request, reason=""):
    """
    Custom ``CSRF_FAILURE_VIEW`` (see ``settings.CSRF_FAILURE_VIEW``).

    Renders a friendly retry page instead of Django's raw 403, and logs the
    failure so CSRF 403s can be measured in production (investigating #599/#623).

    We log whether the CSRF cookie reached the server rather than the token
    value itself: the cookie presence is the most diagnostic signal for the
    cookie-blocking / Secure-cookie theory, and logging secret token values is
    poor practice.
    """
    logger.warning(
        "CSRF verification failed: reason=%r path=%s method=%s "
        "csrf_cookie_present=%s referer=%r user_agent=%r",
        reason,
        request.path,
        request.method,
        "csrftoken" in request.COOKIES,
        request.META.get("HTTP_REFERER"),
        request.META.get("HTTP_USER_AGENT"),
    )
    context = {"reason": reason, "debug": settings.DEBUG}
    return render(request, "csrf_failure.html", context, status=403)


@never_cache
@require_http_methods(["GET", "HEAD"])
def healthz(request):
    """
    Health-check endpoint for uptime monitoring.

    Public (no authentication). Returns 200 if the database answers a trivial
    query, otherwise 503. Failure details are logged, never exposed.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        logger.exception("Health check failed: database unavailable")
        return JsonResponse({"status": "error"}, status=503)
    return JsonResponse({"status": "ok"})
