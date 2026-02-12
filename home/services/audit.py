"""Audit logging service for administrative actions"""

from typing import Any, Dict, Optional
from django.db import models
from ..models import AdminAuditLog, User


class AuditService:
    """Service for creating audit log entries"""

    @staticmethod
    def log_deletion(
        user: User,
        target: models.Model,
        reason: str,
        cascade_info: Optional[Dict[str, int]] = None
    ) -> AdminAuditLog:
        """Log a deletion action with cascade impact details"""
        action_type_map = {
            "User": AdminAuditLog.ActionType.DELETE_USER,
            "Organisation": AdminAuditLog.ActionType.DELETE_ORGANISATION,
            "Project": AdminAuditLog.ActionType.DELETE_PROJECT,
            "Survey": AdminAuditLog.ActionType.DELETE_SURVEY,
        }

        model_name = target.__class__.__name__
        action_type = action_type_map.get(model_name, AdminAuditLog.ActionType.BULK_DELETE)

        return AdminAuditLog.objects.create(
            performed_by=user,
            action_type=action_type,
            target_model=model_name,
            target_id=target.pk,
            target_representation=str(target),
            reason=reason,
            metadata={
                "cascade_deletes": cascade_info or {},
                "object_pk": target.pk,
            }
        )

    @staticmethod
    def log_export(user: User, export_type: str, survey_count: int, response_count: int) -> AdminAuditLog:
        """Log data export action"""
        return AdminAuditLog.objects.create(
            performed_by=user,
            action_type=AdminAuditLog.ActionType.EXPORT_CONSENTED,
            target_model="Survey",
            target_id=None,
            target_representation=f"{survey_count} surveys exported",
            reason=f"Exported consented data for research ({export_type})",
            metadata={
                "export_type": export_type,
                "survey_count": survey_count,
                "response_count": response_count,
            }
        )


audit_service = AuditService()
