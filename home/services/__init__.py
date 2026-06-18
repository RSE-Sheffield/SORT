# Re-export the module-level singletons for use in views
from .data_protection import data_protection_service
from .organisation import organisation_service
from .project import project_service

__all__ = [
    "data_protection_service",
    "project_service",
    "organisation_service",
]
