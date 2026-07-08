from typing import Literal


class OrganisationMembershipRole:
    """
    The permissions that a user may have within an organisation.
    """
    ADMIN = "ADMIN"
    "Full control over organisation and all projects"
    PROJECT_MANAGER = "PROJECT_MANAGER"
    "Can manage specific projects with view or edit permissions"


ROLE_ADMIN = OrganisationMembershipRole.ADMIN
ROLE_PROJECT_MANAGER = OrganisationMembershipRole.PROJECT_MANAGER

# Django choices
ROLES = [
    (ROLE_ADMIN, "Admin"),
    (ROLE_PROJECT_MANAGER, "Project Manager"),
]
"""
ADMIN: Full control over organisation and all projects
PROJECT_MANAGER: Can manage specific projects with view or edit permissions
"""

RoleType = Literal["ADMIN", "PROJECT_MANAGER"]

PERMISSION_VIEW = "VIEW"
PERMISSION_EDIT = "EDIT"

PERMISSION_CHOICES = [
    (PERMISSION_VIEW, "View Only"),
    (PERMISSION_EDIT, "View and Edit"),
]

# Email domain used to anonymise a user's address on GDPR erasure (see
# UserService.anonymise). Used to distinguish erased accounts from merely
# suspended ones, since both share is_active=False.
DELETED_ACCOUNT_EMAIL_DOMAIN = "deleted.invalid"
