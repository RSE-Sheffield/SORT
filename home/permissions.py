from typing import Optional, Dict
from django.db.models.query import QuerySet
from .models import GuestProjectAccess, OrganisationMembership, Project, User
from .constants import ROLE_ADMIN, ROLE_MEMBER, ROLE_GUEST, RoleType


def get_user_role_in_project(user: User, project: Project) -> Optional[RoleType]:
    """Get user's role in the project's organisations"""
    user_org = (
        project.projectorganisation_set.filter(
            organisation__organisationmembership__user=user
        )
        .select_related("organisation")
        .first()
    )

    if not user_org:
        return None

    return user_org.organisation.get_user_role(user)


def can_view_project(user: User, project: Project) -> bool:
    """
    Check if user can view the project:
        - ADMIN/MEMBER: Can always view if they're in the project's organisations
        - GUEST: Can view if they have explicit VIEW or EDIT access
    """
    role = get_user_role_in_project(user, project)

    if not role:
        return False

    if role in [ROLE_ADMIN, ROLE_MEMBER]:
        return True
    elif role == ROLE_GUEST:
        return GuestProjectAccess.objects.filter(user=user, project=project).exists()

    return False


def can_edit_project(user: User, project: Project) -> bool:
    """
    Check if user can edit the project:
        - ADMIN/MEMBER: Can always edit if they're in the project's organisations
        - GUEST: Can only edit if they have explicit EDIT access
    """
    role = get_user_role_in_project(user, project)

    if not role:
        return False

    if role in [ROLE_ADMIN, ROLE_MEMBER]:
        return True
    elif role == ROLE_GUEST:
        return GuestProjectAccess.objects.filter(
            user=user, project=project, permission="EDIT"
        ).exists()

    return False


def can_create_projects(user: User) -> bool:
    """Check if user can create projects based on admin role"""
    return OrganisationMembership.objects.filter(user=user, role=ROLE_ADMIN).exists()


def get_project_permissions(user: User, projects: QuerySet[Project]) -> Dict[int, bool]:
    """Get edit permissions for multiple projects"""
    return {project.id: can_edit_project(user, project) for project in projects}
