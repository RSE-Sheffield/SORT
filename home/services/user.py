import logging
import uuid
from typing import Optional

import django.core.mail
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction

from ..constants import DELETED_ACCOUNT_EMAIL_DOMAIN, ROLE_ADMIN
from ..models import DataProtectionEvent, ErasureRequest, OrganisationMembership, Project, User
from .data_protection import data_protection_service
from .organisation import organisation_service

logger = logging.getLogger(__name__)


def notify_staff_of_pending_erasure(user: User) -> None:
    """
    Alert staff that a self-service erasure request needs manual action
    (see UserService.request_self_erasure). Follows the same plain
    ``send_mail`` pattern used for survey invitations (survey/views.py) —
    there's no shared notification service yet.
    """
    staff_emails = list(
        User.objects.filter(is_staff=True, is_active=True).values_list("email", flat=True)
    )
    if not staff_emails:
        return

    try:
        django.core.mail.send_mail(
            subject="SORT: account erasure request needs action",
            message=(
                f"{user} ({user.email}) has requested account erasure but is the "
                "sole admin of an organisation with other members, so it could not "
                "be completed automatically.\n\n"
                "UK GDPR Art. 12(3) requires this to be actioned within one month "
                "of the request. Please review and complete it via the console: "
                f"/console/users/{user.pk}/"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=staff_emails,
            fail_silently=False,
        )
    except Exception:
        # The ErasureRequest is already recorded and listed on the console
        # dashboard, so a mail outage mustn't surface as an error to the user.
        logger.exception("Failed to notify staff of pending erasure request for user %s", user.pk)


class UserService:
    def anonymise(self, user: User, *, requested_by: Optional[User], actioned_by: User) -> None:
        original_email = user.email
        user.first_name = "Deleted"
        user.last_name = "User"
        user.email = f"deleted-{uuid.uuid4().hex}@{DELETED_ACCOUNT_EMAIL_DOMAIN}"
        user.is_active = False
        user.set_unusable_password()
        user.save()
        OrganisationMembership.objects.filter(user=user).delete()
        data_protection_service.record_event(
            event_type=DataProtectionEvent.EventType.ERASURE,
            subject_user=user,
            subject_email=original_email,
            requested_by=requested_by,
            actioned_by=actioned_by,
        )

    def request_self_erasure(self, user: User) -> bool:
        """
        Self-service GDPR erasure/consent-withdrawal (UK GDPR Art. 7(3),
        17(1)(b)). Returns True if the account was erased immediately, or
        False if it was deferred to staff because `user` is the sole admin
        of an organisation with other members — erasing them immediately
        would leave that organisation unmanageable.

        Staff and superuser accounts can't erase themselves this way — like
        the console's "Delete user" action, another staff member must do it.
        """
        if user.is_staff or user.is_superuser:
            raise PermissionDenied("Staff accounts must be erased by another staff member")

        with transaction.atomic():
            # Lock the memberships of every org this user admins so a
            # concurrent membership change can't invalidate the check below
            # between it running and the erasure being applied.
            admin_org_ids = OrganisationMembership.objects.filter(user=user, role=ROLE_ADMIN).values(
                "organisation_id"
            )
            list(OrganisationMembership.objects.select_for_update().filter(organisation_id__in=admin_org_ids))

            if organisation_service.get_sole_admin_orgs_with_other_members(user).exists():
                _, created = ErasureRequest.objects.get_or_create(user=user, status=ErasureRequest.Status.PENDING)
                # Repeat submissions (double-click, retry) shouldn't re-alert staff.
                if created:
                    transaction.on_commit(lambda: notify_staff_of_pending_erasure(user))
                return False

            self.anonymise(user, requested_by=user, actioned_by=user)
            return True

    def update_user(self, user: User, *, first_name: str, last_name: str, email: str) -> User:
        """
        Apply a corrected name/email to ``user`` (UK GDPR Art. 16 Right to
        Rectification). Callers are responsible for enforcing permission and
        recording any audit event.
        """
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save(update_fields=["first_name", "last_name", "email"])
        return user

    def export_personal_data(self, user: User) -> dict:
        """
        Build a UK GDPR Art. 15 subject access export of ``user``'s personal data.

        Only records belonging to ``user`` are included — e.g. other members
        of a shared organisation are deliberately excluded.
        """
        memberships = OrganisationMembership.objects.filter(user=user).select_related("organisation")
        projects = Project.objects.filter(created_by=user).select_related("organisation")
        return {
            "profile": {
                "id": user.pk,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "date_joined": user.date_joined,
                "last_login": user.last_login,
                "is_active": user.is_active,
            },
            "organisation_memberships": [
                {
                    "organisation": membership.organisation.name,
                    "role": membership.role,
                    "joined_at": membership.joined_at,
                }
                for membership in memberships
            ],
            "projects_created": [
                {
                    "organisation": project.organisation.name,
                    "name": project.name,
                    "description": project.description,
                    "created_at": project.created_at,
                }
                for project in projects
            ],
        }


user_service = UserService()
