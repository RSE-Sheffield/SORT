from typing import Any

from home.services import BasePermissionService
from home.models import User


class SurveyService(BasePermissionService):

    def can_view(self, user: User, instance: Any) -> bool:
        return True
    def can_create(self, user: User) -> bool:
        # TODO: Requires checking that project
        return True

    def can_edit(self, user: User, instance: Any) -> bool:
        return True
    def can_delete(self, user: User, instance: Any) -> bool:
        return True
