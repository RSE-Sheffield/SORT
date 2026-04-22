from .base import BasePermissionService
from .data_protection import DataProtectionService, data_protection_service
from .organisation import OrganisationService, organisation_service
from .project import ProjectService, project_service

# Create instances for use in views


__all__ = [
    "BasePermissionService",
    "DataProtectionService",
    "ProjectService",
    "OrganisationService",
    "data_protection_service",
    "project_service",
    "organisation_service",
]
