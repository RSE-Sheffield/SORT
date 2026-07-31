import uuid

from ..constants import DELETED_ACCOUNT_EMAIL_DOMAIN
from ..models import OrganisationMembership, Project, User


class UserService:
    def anonymise(self, user: User) -> None:
        user.first_name = "Deleted"
        user.last_name = "User"
        user.email = f"deleted-{uuid.uuid4().hex}@{DELETED_ACCOUNT_EMAIL_DOMAIN}"
        user.is_active = False
        user.set_unusable_password()
        user.save()
        OrganisationMembership.objects.filter(user=user).delete()

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
