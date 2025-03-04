from .base import BasePermissionService
from .organisation import OrganisationService
from .project import ProjectService

# Create instances for use in views
project_service = ProjectService()
organisation_service = OrganisationService()

__all__ = [
    "BasePermissionService",
    "ProjectService",
    "OrganisationService",
    "project_service",
    "organisation_service",
]
