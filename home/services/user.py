import uuid

from ..models import OrganisationMembership, User


class UserService:
    def anonymise_user(self, user: User) -> None:
        user.first_name = ""
        user.last_name = ""
        user.email = f"deleted-{uuid.uuid4().hex}@deleted.invalid"
        user.is_active = False
        user.set_unusable_password()
        user.save()
        OrganisationMembership.objects.filter(user=user).delete()


user_service = UserService()
