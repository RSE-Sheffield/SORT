from .base import BasePermissionService
from .project import ProjectService
from .organisation import OrganisationService

# Create instances for use in views
project_service = ProjectService()
organisation_service = OrganisationService()

__all__ = [
    'BasePermissionService',
    'ProjectService',
    'OrganisationService',
    'project_service',
    'organisation_service'
]
