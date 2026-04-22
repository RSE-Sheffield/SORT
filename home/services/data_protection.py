"""
Data protection event service.

Records actions taken on users' personal data (erasure, export, restriction,
consent withdrawal) for UK GDPR Article 5(2) accountability. The log is
append-only; see `DataProtectionEvent.save`/`delete`.
"""

from datetime import datetime
from typing import Optional

from django.core.exceptions import PermissionDenied
from django.db.models.query import QuerySet

from ..models import DataProtectionEvent, User


class DataProtectionService:
    """Service for recording and querying data protection events.

    `record_event` is deliberately not permission-gated — the calling flow
    has already performed its own permission checks, and the audit record
    must be written even if the caller is e.g. a system task. Read access
    (`list_events`) is gated on staff status.
    """

    def record_event(
        self,
        *,
        event_type: str,
        subject_user: User,
        actioned_by: Optional[User],
        requested_by: Optional[User] = None,
        requested_at: Optional[datetime] = None,
        notes: str = "",
    ) -> DataProtectionEvent:
        subject_email = getattr(subject_user, "email", None)
        subject_identifier = (
            subject_email if subject_email else f"deleted-user-{subject_user.pk}"
        )
        return DataProtectionEvent.objects.create(
            event_type=event_type,
            subject_user_id=getattr(subject_user, "pk", None),
            subject_identifier=subject_identifier,
            actioned_by=actioned_by,
            requested_by=requested_by,
            requested_at=requested_at,
            notes=notes,
        )

    def list_events(
        self,
        user: User,
        *,
        event_type: Optional[str] = None,
        subject_user_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> QuerySet[DataProtectionEvent]:
        if not (user.is_authenticated and user.is_active and user.is_staff):
            raise PermissionDenied(
                "Only active staff may read the data protection log"
            )

        qs = DataProtectionEvent.objects.select_related(
            "actioned_by", "requested_by"
        )
        if event_type:
            qs = qs.filter(event_type=event_type)
        if subject_user_id:
            qs = qs.filter(subject_user_id=subject_user_id)
        if date_from:
            qs = qs.filter(actioned_at__gte=date_from)
        if date_to:
            qs = qs.filter(actioned_at__lte=date_to)
        return qs


data_protection_service = DataProtectionService()
