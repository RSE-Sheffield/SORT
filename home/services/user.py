import uuid

from ..constants import DELETED_EMAIL_DOMAIN
from ..models import OrganisationMembership, User


class UserService:
    def anonymise(self, user: User) -> None:
        user.first_name = "Deleted"
        user.last_name = "User"
        user.email = f"deleted-{uuid.uuid4().hex}@{DELETED_EMAIL_DOMAIN}"
        user.is_active = False
        user.set_unusable_password()
        user.save()
        OrganisationMembership.objects.filter(user=user).delete()


user_service = UserService()
