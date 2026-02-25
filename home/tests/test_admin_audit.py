"""Tests for admin audit logging service"""
from django.test import TestCase

from home.models import AdminAuditLog
from home.services import audit_service
from SORT.test.model_factory import SuperUserFactory, OrganisationFactory, UserFactory


class AuditServiceTestCase(TestCase):
    """Test cases for audit logging service"""

    def setUp(self):
        self.superuser = SuperUserFactory()
        self.organisation = OrganisationFactory()
        self.user = UserFactory()

    def test_log_deletion_organisation(self):
        """Test audit log creation for organisation deletion"""
        log = audit_service.log_deletion(
            user=self.superuser,
            target=self.organisation,
            reason="Test deletion - spurious organisation",
            cascade_info={"projects": 3, "surveys": 5}
        )

        self.assertEqual(log.action_type, AdminAuditLog.ActionType.DELETE_ORGANISATION)
        self.assertEqual(log.performed_by, self.superuser)
        self.assertEqual(log.target_model, "Organisation")
        self.assertEqual(log.target_id, self.organisation.pk)
        self.assertEqual(log.reason, "Test deletion - spurious organisation")
        self.assertEqual(log.metadata["cascade_deletes"]["projects"], 3)
        self.assertEqual(log.metadata["cascade_deletes"]["surveys"], 5)

    def test_log_deletion_user(self):
        """Test audit log creation for user deletion"""
        log = audit_service.log_deletion(
            user=self.superuser,
            target=self.user,
            reason="User requested account deletion",
            cascade_info={"organisations": 1}
        )

        self.assertEqual(log.action_type, AdminAuditLog.ActionType.DELETE_USER)
        self.assertEqual(log.performed_by, self.superuser)
        self.assertEqual(log.target_model, "User")
        self.assertEqual(log.target_representation, str(self.user))

    def test_log_export(self):
        """Test audit log creation for data export"""
        log = audit_service.log_export(
            user=self.superuser,
            export_type="CSV",
            survey_count=10,
            response_count=50
        )

        self.assertEqual(log.action_type, AdminAuditLog.ActionType.EXPORT_CONSENTED)
        self.assertEqual(log.performed_by, self.superuser)
        self.assertEqual(log.target_model, "Survey")
        self.assertIn("10 surveys exported", log.target_representation)
        self.assertEqual(log.metadata["export_type"], "CSV")
        self.assertEqual(log.metadata["survey_count"], 10)
        self.assertEqual(log.metadata["response_count"], 50)

    def test_audit_log_ordering(self):
        """Test that audit logs are ordered by timestamp descending"""
        log1 = audit_service.log_deletion(
            user=self.superuser,
            target=self.organisation,
            reason="First deletion"
        )
        log2 = audit_service.log_deletion(
            user=self.superuser,
            target=self.user,
            reason="Second deletion"
        )

        logs = AdminAuditLog.objects.all()
        self.assertEqual(logs[0].pk, log2.pk)  # Most recent first
        self.assertEqual(logs[1].pk, log1.pk)


class AdminAuditLogAdminTestCase(TestCase):
    """Test cases for AdminAuditLog admin interface"""

    def setUp(self):
        self.superuser = SuperUserFactory()
        self.organisation = OrganisationFactory()

    def test_audit_log_immutable(self):
        """Verify audit logs cannot be modified via admin"""
        from home.admin import AdminAuditLogAdmin
        from django.contrib.admin.sites import site

        admin_instance = AdminAuditLogAdmin(AdminAuditLog, site)

        # Cannot add new logs via admin
        self.assertFalse(admin_instance.has_add_permission(None))

        # Cannot delete logs
        self.assertFalse(admin_instance.has_delete_permission(None))

        # Cannot edit logs
        self.assertFalse(admin_instance.has_change_permission(None))

    def test_audit_log_str_representation(self):
        """Test string representation of audit log"""
        log = audit_service.log_deletion(
            user=self.superuser,
            target=self.organisation,
            reason="Test"
        )

        log_str = str(log)
        self.assertIn(str(self.superuser), log_str)
        self.assertIn("DELETE_ORG", log_str)
