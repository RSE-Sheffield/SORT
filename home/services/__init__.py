from .base import BaseService
from .project import ProjectService
from .organisation import OrganisationService

# Create instances for use in views
project_service = ProjectService()
organisation_service = OrganisationService()

__all__ = [
    'BaseService',
    'ProjectService',
    'OrganisationService',
    'project_service',
    'organisation_service'
]