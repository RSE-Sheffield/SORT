from typing import Literal

ROLE_ADMIN = "ADMIN"
ROLE_MEMBER = "MEMBER"
ROLE_GUEST = "GUEST"

ROLES = [
    (ROLE_ADMIN, "Admin"),
    (ROLE_MEMBER, "Member"),
    (ROLE_GUEST, "Guest"),
]
"""
ADMIN: Full control
MEMBER: Can view and edit projects
GUEST: Can view certain projects
"""


RoleType = Literal["ADMIN", "MEMBER", "GUEST"]