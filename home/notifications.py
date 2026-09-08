"""
Email notifications for organisation join requests.

This is a plain module rather than a service because there is nothing here to
permission-gate — it is I/O adaptation, not business logic — and keeping it out
of ``home.services`` avoids an import cycle with the views.

Failure policy — deliberately different from the member-invite flow in
``home.views.organisation``, which deletes the Invitation when its email fails
to send. That is right there because an invitation *is* its email: the tokenised
link is the only way to use it, so an unsent invitation is useless. A join
request is durable application state instead: the requester sees it under "My
requests", administrators see it in their review queue, and approval works
whether or not any email was delivered. So the notification helpers here are
called from the view *after* the service has committed, never inside its
transaction (SMTP can block for EMAIL_TIMEOUT while holding row locks), and a
send failure is logged and surfaced as a warning message — never rolled back.
Revoking a just-granted membership because the mail server was down would be
strictly worse than a missing email.
"""

import logging
import smtplib
from typing import List, Optional, Tuple

from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.urls import reverse

from .constants import DELETED_ACCOUNT_EMAIL_DOMAIN, ROLE_ADMIN
from .models import OrganisationJoinRequest, User

logger = logging.getLogger(__name__)

SUBMITTED_SUBJECT_TEMPLATE = "home/email/join_request_submitted_subject.txt"
SUBMITTED_BODY_TEMPLATE = "home/email/join_request_submitted_body.txt"
DECISION_SUBJECT_TEMPLATE = "home/email/join_request_decision_subject.txt"
DECISION_BODY_TEMPLATE = "home/email/join_request_decision_body.txt"


def render_email(
    subject_template: str, body_template: str, context: dict
) -> Tuple[str, str]:
    """
    Render an email's subject and body from templates.

    The subject is collapsed onto one line (as Django's own PasswordResetForm
    does) and prefixed with settings.EMAIL_SUBJECT_PREFIX, which send_mail()
    does not apply — only mail_admins()/mail_managers() do.
    """
    subject = render_to_string(subject_template, context)
    subject = "".join(subject.splitlines()).strip()
    body = render_to_string(body_template, context)
    return f"{settings.EMAIL_SUBJECT_PREFIX}{subject}", body


def send_templated_mail(
    *,
    subject_template: str,
    body_template: str,
    context: dict,
    recipient_list: List[str],
) -> int:
    """
    Send one email per recipient and return how many were sent.

    One message per recipient, rather than a single message addressed to all of
    them, so recipients' email addresses are not disclosed to each other. A
    failure for one recipient is logged and the remaining recipients are still
    attempted.
    """
    subject, body = render_email(subject_template, body_template, context)
    sent = 0
    for recipient in recipient_list:
        try:
            sent += send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
        except (smtplib.SMTPException, OSError):
            logger.exception(
                "Failed to send email (subject=%s, to=%s)", subject, recipient
            )
    return sent


def get_organisation_admin_emails(organisation) -> List[str]:
    """
    Email addresses of the administrators who can act on a join request.

    Suspended accounts are excluded because they cannot log in to act, and
    erased accounts because their anonymised addresses are unroutable.
    """
    return list(
        User.objects.filter(
            organisationmembership__organisation=organisation,
            organisationmembership__role=ROLE_ADMIN,
            is_active=True,
        )
        .exclude(email__endswith=f"@{DELETED_ACCOUNT_EMAIL_DOMAIN}")
        .values_list("email", flat=True)
        .distinct()
    )


def _absolute_url(view_name: str, request: Optional[HttpRequest]) -> str:
    """Build a link for an email body.

    django.contrib.sites is not installed, so there is no Site to fall back on;
    the request is the only source of the host name.
    """
    path = reverse(view_name)
    if request is None:
        logger.warning(
            "No request available to build an absolute URL for %s; "
            "sending a relative link instead",
            view_name,
        )
        return path
    return request.build_absolute_uri(path)


def notify_admins_of_join_request(
    join_request: OrganisationJoinRequest, request: Optional[HttpRequest] = None
) -> int:
    """Tell an organisation's administrators that someone wants to join."""
    recipient_list = get_organisation_admin_emails(join_request.organisation)
    if not recipient_list:
        logger.warning(
            "Organisation %s has no active administrators to notify about "
            "join request %s",
            join_request.organisation_id,
            join_request.pk,
        )
        return 0

    return send_templated_mail(
        subject_template=SUBMITTED_SUBJECT_TEMPLATE,
        body_template=SUBMITTED_BODY_TEMPLATE,
        context={
            "join_request": join_request,
            "review_url": _absolute_url("join_requests", request),
        },
        recipient_list=recipient_list,
    )


def notify_requester_of_join_decision(
    join_request: OrganisationJoinRequest, request: Optional[HttpRequest] = None
) -> int:
    """Tell the requester whether their request was approved or rejected."""
    return send_templated_mail(
        subject_template=DECISION_SUBJECT_TEMPLATE,
        body_template=DECISION_BODY_TEMPLATE,
        context={
            "join_request": join_request,
            "is_approved": join_request.status
            == OrganisationJoinRequest.Status.APPROVED,
            "dashboard_url": _absolute_url("dashboard", request),
            "requests_url": _absolute_url("join_requests_mine", request),
        },
        recipient_list=[join_request.user.email],
    )
