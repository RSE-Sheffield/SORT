from .data_protection import DataProtectionService
from .organisation import OrganisationService
from .project import ProjectService

# Create instances for use in views
data_protection_service = DataProtectionService()
organisation_service = OrganisationService()
project_service = ProjectService()

__all__ = [
    "data_protection_service",
    "project_service",
    "organisation_service",
]
