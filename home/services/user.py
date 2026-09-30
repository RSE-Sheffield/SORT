import uuid

import django.core.mail
from django.conf import settings

from ..constants import DELETED_ACCOUNT_EMAIL_DOMAIN
from ..models import DataProtectionEvent, ErasureRequest, OrganisationMembership, Project, User
from .data_protection import data_protection_service
from .organisation import organisation_service


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


class UserService:
    def anonymise(self, user: User, *, requested_by: User, actioned_by: User) -> None:
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
        """
        if organisation_service.get_sole_admin_orgs_with_other_members(user).exists():
            ErasureRequest.objects.get_or_create(user=user, status=ErasureRequest.Status.PENDING)
            notify_staff_of_pending_erasure(user)
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
