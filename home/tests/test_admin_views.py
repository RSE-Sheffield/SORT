"""Tests for custom admin views"""
from django.test import TestCase, Client
from django.urls import reverse

from home.models import AdminAuditLog
from SORT.test.model_factory import (
    SuperUserFactory,
    UserFactory,
    OrganisationFactory,
    ProjectFactory,
    SurveyFactory,
)


class AdminDashboardTestCase(TestCase):
    """Test cases for admin dashboard view"""

    def setUp(self):
        self.client = Client()
        self.superuser = SuperUserFactory()
        self.normal_user = UserFactory()

    def test_dashboard_access_superuser(self):
        """Superuser can access admin dashboard"""
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin Dashboard")
        self.assertContains(response, "Platform Statistics")

    def test_dashboard_denied_normal_user(self):
        """Normal users denied access to dashboard"""
        self.client.force_login(self.normal_user)
        response = self.client.get(reverse("admin_dashboard"))

        # @staff_member_required redirects non-staff users
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/", response.url)

    def test_dashboard_denied_anonymous(self):
        """Anonymous users redirected to login"""
        response = self.client.get(reverse("admin_dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_dashboard_statistics(self):
        """Dashboard displays correct statistics"""
        # Create test data
        org = OrganisationFactory()
        project = ProjectFactory(organisation=org)
        survey = SurveyFactory(project=project, is_shared=True)

        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin_dashboard"))

        self.assertIn("stats", response.context)
        stats = response.context["stats"]

        # Verify key stats are present and reasonable
        self.assertGreaterEqual(stats["total_organisations"], 1)
        self.assertGreaterEqual(stats["total_projects"], 1)
        self.assertGreaterEqual(stats["total_surveys"], 1)
        self.assertGreaterEqual(stats["consented_surveys"], 1)


class ConsentedDataExportTestCase(TestCase):
    """Test cases for consented data export functionality"""

    def setUp(self):
        self.client = Client()
        self.superuser = SuperUserFactory()
        self.normal_user = UserFactory()

        # Create test surveys
        org = OrganisationFactory()
        project = ProjectFactory(organisation=org)
        self.consented_survey = SurveyFactory(project=project, is_shared=True)
        self.non_consented_survey = SurveyFactory(project=project, is_shared=False)

    def test_export_csv_superuser_only(self):
        """Only superusers can export consented data"""
        self.client.force_login(self.normal_user)
        response = self.client.get(reverse("admin_export_consented_data") + "?format=csv")

        # @staff_member_required redirects non-staff users
        self.assertEqual(response.status_code, 302)

    def test_export_csv_only_consented(self):
        """Export includes only consented surveys"""
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin_export_consented_data") + "?format=csv")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn(".csv", response["Content-Disposition"])

        # Verify audit log created
        audit_log = AdminAuditLog.objects.filter(
            action_type=AdminAuditLog.ActionType.EXPORT_CONSENTED
        ).first()
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.performed_by, self.superuser)
        self.assertEqual(audit_log.metadata["export_type"], "CSV")

    def test_export_excel_format(self):
        """Export in Excel format works"""
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin_export_consented_data") + "?format=excel")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        self.assertIn(".xlsx", response["Content-Disposition"])

    def test_export_no_consented_surveys(self):
        """Export handles case with no consented surveys"""
        # Mark all surveys as non-consented
        self.consented_survey.is_shared = False
        self.consented_survey.save()

        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin_export_consented_data") + "?format=csv")

        # Should redirect with warning message
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/survey/survey/", response.url)

    def test_export_invalid_format(self):
        """Export handles invalid format parameter"""
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin_export_consented_data") + "?format=invalid")

        self.assertEqual(response.status_code, 302)


class DeleteWithReasonTestCase(TestCase):
    """Test cases for safe deletion with audit logging"""

    def setUp(self):
        self.client = Client()
        self.superuser = SuperUserFactory()
        self.normal_user = UserFactory()
        self.org = OrganisationFactory()

    def test_delete_view_access_superuser_only(self):
        """Only superusers can access delete with reason view"""
        self.client.force_login(self.normal_user)
        response = self.client.get(
            reverse("admin_delete_with_reason", kwargs={"model_name": "organisation"})
            + f"?ids={self.org.pk}"
        )

        # @staff_member_required redirects non-staff users
        self.assertEqual(response.status_code, 302)

    def test_delete_view_get_shows_confirmation(self):
        """GET request shows confirmation page"""
        self.client.force_login(self.superuser)
        response = self.client.get(
            reverse("admin_delete_with_reason", kwargs={"model_name": "organisation"})
            + f"?ids={self.org.pk}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Delete Organisation")
        self.assertContains(response, str(self.org))
        self.assertContains(response, "Reason for deletion")

    def test_delete_view_post_requires_reason(self):
        """POST without reason shows error"""
        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse("admin_delete_with_reason", kwargs={"model_name": "organisation"})
            + f"?ids={self.org.pk}",
            data={"reason": ""}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reason is required")

    def test_delete_view_post_with_reason_deletes(self):
        """POST with reason deletes and creates audit log"""
        org_pk = self.org.pk
        org_name = str(self.org)

        self.client.force_login(self.superuser)
        response = self.client.post(
            reverse("admin_delete_with_reason", kwargs={"model_name": "organisation"})
            + f"?ids={org_pk}",
            data={"reason": "Test deletion - spurious organisation"}
        )

        # Should redirect to changelist
        self.assertEqual(response.status_code, 302)

        # Organisation should be deleted
        from home.models import Organisation
        self.assertFalse(Organisation.objects.filter(pk=org_pk).exists())

        # Audit log should exist
        audit_log = AdminAuditLog.objects.filter(
            action_type=AdminAuditLog.ActionType.DELETE_ORGANISATION,
            target_id=org_pk
        ).first()
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.performed_by, self.superuser)
        self.assertEqual(audit_log.reason, "Test deletion - spurious organisation")
        self.assertEqual(audit_log.target_representation, org_name)

    def test_delete_view_no_ids_parameter(self):
        """View handles missing ids parameter"""
        self.client.force_login(self.superuser)
        response = self.client.get(
            reverse("admin_delete_with_reason", kwargs={"model_name": "organisation"})
        )

        self.assertEqual(response.status_code, 302)

    def test_delete_view_invalid_model_name(self):
        """View handles invalid model name"""
        self.client.force_login(self.superuser)
        response = self.client.get(
            reverse("admin_delete_with_reason", kwargs={"model_name": "invalid"})
            + "?ids=1"
        )

        self.assertEqual(response.status_code, 302)

    def test_delete_cascade_impact_calculated(self):
        """Cascade impact is calculated and displayed"""
        # Create related objects
        project = ProjectFactory(organisation=self.org)
        survey = SurveyFactory(project=project)

        self.client.force_login(self.superuser)
        response = self.client.get(
            reverse("admin_delete_with_reason", kwargs={"model_name": "organisation"})
            + f"?ids={self.org.pk}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cascade Deletion Impact")
        # Should show project and survey counts
        self.assertIn("cascade_info", response.context)
