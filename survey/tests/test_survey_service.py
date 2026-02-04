"""
Unit tests for the survey service
"""

import json

import django.contrib.auth.models
import django.core.exceptions
import django.test

import SORT.test.model_factory
import SORT.test.test_case
from home.constants import ROLE_ADMIN
from survey.models import (
    Invitation,
    Survey,
    SurveyEvidenceSection,
    SurveyImprovementPlanSection,
    SurveyResponse,
)
from survey.services import SurveyService


class SurveyServiceTestCase(SORT.test.test_case.ServiceTestCase):
    def setUp(self):
        self.client = django.test.Client()
        self.service = SurveyService()
        self.invitation = SORT.test.model_factory.InvitationFactory()
        self.survey = self.invitation.survey
        self.project = self.survey.project
        self.organisation = self.project.organisation
        self.admin = self.organisation.members.first()
        self.anonymous_user = SORT.test.model_factory.UserFactory()

    def test_get_user_role(self):
        role = self.service.get_user_role(user=self.admin, survey=self.survey)
        self.assertIsInstance(role, str)
        self.assertEqual(role, ROLE_ADMIN)

    def test_can_view(self):
        self.assertTrue(self.service.can_view(user=self.admin, survey=self.survey))

    def test_can_view_unauthorised(self):
        """
        Check that a user that isn't part of the organisation can't view a survey
        """
        self.assertFalse(
            self.service.can_view(user=self.anonymous_user, survey=self.survey)
        )

    def test_can_edit(self):
        self.assertTrue(self.service.can_edit(user=self.admin, survey=self.survey))

    def test_can_edit_unauthorised(self):
        self.assertFalse(
            self.service.can_edit(user=self.anonymous_user, survey=self.survey)
        )

    def test_can_delete(self):
        self.assertTrue(self.service.can_delete(user=self.admin, survey=self.survey))

    def test_can_delete_unauthorised(self):
        self.assertFalse(
            self.service.can_delete(user=self.anonymous_user, survey=self.survey)
        )

    def test_can_create(self):
        self.assertTrue(self.service.can_create(self.admin, self.project))

    def test_can_create_unauthorised(self):
        self.assertFalse(self.service.can_create(self.anonymous_user, self.project))

    def test_get_survey(self):
        self.assertIsInstance(self.survey.pk, int)
        survey = self.service.get_survey(user=self.admin, survey_id=self.survey.pk)
        self.assertIsInstance(survey, Survey)
        self.assertEqual(survey.pk, self.survey.pk)

    def test_get_survey_unauthorised(self):
        with self.assertRaises(django.core.exceptions.PermissionDenied):
            self.service.get_survey(user=self.anonymous_user, survey_id=self.survey.pk)

    def test_initialise_survey(self):
        self.service.initialise_survey(
            user=self.admin, project=self.project, survey=self.survey
        )

        self.assertIsInstance(self.survey.survey_config, dict)
        self.assertIsInstance(self.survey.consent_config_default, dict)
        self.assertIsInstance(self.survey.survey_config, dict)

        # Check that a survey was created with some sections
        self.assertGreater(len(self.survey.survey_config["sections"]), 0)

    def test_update_consent_demography_config(self):
        self.service.update_consent_demography_config(
            user=self.admin,
            survey=self.survey,
            consent_config=dict(sections=list()),
            demography_config=dict(sections=list()),
            survey_body_path="Nurses",
        )

        self.assertIsInstance(self.survey.survey_config, dict)

        # There should be some SORT survey sections
        self.assertGreater(
            len(self.survey.survey_config["sections"]), 0, "No survey sections"
        )

    def test_duplicate_survey(self):
        # Properly initialise the survey
        self.service.initialise_survey(self.admin, self.project, self.survey)
        self.service.update_consent_demography_config(
            self.admin,
            self.survey,
            demography_config=self.survey.demography_config_default,
            survey_body_path=self.survey.survey_body_path,
            consent_config=self.survey.consent_config_default,
        )

        duplicated_survey = self.service.duplicate_survey(
            user=self.admin, survey=self.survey
        )
        self.assertTrue(duplicated_survey.name.startswith("Copy of"))
        self.assertEqual(duplicated_survey.project, self.survey.project)
        self.assertDictEqual(duplicated_survey.survey_config, self.survey.survey_config)
        self.assertDictEqual(
            duplicated_survey.consent_config_default, self.survey.consent_config_default
        )
        self.assertDictEqual(
            duplicated_survey.demography_config_default, self.survey.demography_config_default
        )
        self.assertTrue(
            SurveyEvidenceSection.objects.filter(survey=duplicated_survey).count() > 1
        )
        self.assertTrue(
            SurveyImprovementPlanSection.objects.filter(
                survey=duplicated_survey
            ).count()
            > 1
        )

    def test_get_survey_from_token(self):
        token = self.survey.current_invite_token()
        self.assertIsInstance(token, str)
        survey = self.service.get_survey_from_token(token=token)
        self.assertIsInstance(survey, Survey)

    def test_accept_response(self):
        self.service.accept_response(
            survey=self.survey, responseValues=json.dumps("[]")
        )
        self.assertTrue(self.survey.survey_response.exists())

    def test_create_invitation(self):
        self.service.create_invitation(user=self.admin, survey=self.survey)
        self.service.create_invitation(user=self.admin, survey=self.survey)
        invitation = self.service.create_invitation(user=self.admin, survey=self.survey)
        self.assertIsInstance(invitation, Invitation)

        # The old invitations should be expired, except for the latest one
        # True, True, True, False
        used_values = tuple(self.survey.invitation_set.values_list("used", flat=True))
        for used in used_values[:-1]:
            self.assertTrue(used)
        self.assertFalse(used_values[-1])

    def test_export_csv(self):
        self.service.initialise_survey(
            user=self.admin, project=self.project, survey=self.survey
        )
        csv_data = self.service.export_csv(user=self.admin, survey=self.survey)
        self.assertIsInstance(csv_data, str)

    def test_mock_responses(self):
        self.skipTest("Not yet implemented")
        self.service.generate_mock_responses(
            user=self.admin, survey=self.survey, num_responses=3
        )

    def test_create_survey_evidence_sections(self):
        self.service.initialise_survey(
            user=self.admin, project=self.project, survey=self.survey
        )
        self.service.update_consent_demography_config(
            user=self.admin,
            survey=self.survey,
            consent_config=self.survey.consent_config_default,
            demography_config=self.survey.demography_config_default,
            survey_body_path="Nurses",
        )
        # from survey.models import SurveyEvidenceSection
        # evidence_sections = SurveyEvidenceSection.objects.filter(survey=self.survey).order_by("section_id")
        # self.assertEqual(evidence_sections.count(), len(self.survey.survey_config["sections"]))
        self.assertGreater(self.survey.evidence_sections.count(), 0)
        sort_sections = [
            section
            for section in self.survey.survey_config["sections"]
            if section["type"] == "sort"
        ]
        self.assertEqual(self.survey.evidence_sections.count(), len(sort_sections))

    def test_update_consent_demography_config_with_responses_denied(self):
        """Test that updating config is denied when survey has responses"""
        self.service.initialise_survey(
            user=self.admin, project=self.project, survey=self.survey
        )

        # Add a response to the survey
        self.service.accept_response(
            survey=self.survey, responseValues=json.dumps([])
        )

        # Now try to update config - should fail
        with self.assertRaises(django.core.exceptions.PermissionDenied):
            self.service.update_consent_demography_config(
                user=self.admin,
                survey=self.survey,
                consent_config=dict(sections=list()),
                demography_config=dict(sections=list()),
                survey_body_path="Nurses",
            )

    def test_update_evidence_section(self):
        """Test updating evidence section text"""
        self.service.initialise_survey(
            user=self.admin, project=self.project, survey=self.survey
        )
        self.service.update_consent_demography_config(
            user=self.admin,
            survey=self.survey,
            consent_config=self.survey.consent_config_default,
            demography_config=self.survey.demography_config_default,
            survey_body_path="Nurses",
        )

        evidence_section = self.survey.evidence_sections.first()
        self.assertIsNotNone(evidence_section)

        new_text = "This is updated evidence text"
        self.service.update_evidence_section(
            user=self.admin,
            survey=self.survey,
            evidence_section=evidence_section,
            text=new_text,
        )

        evidence_section.refresh_from_db()
        self.assertEqual(evidence_section.text, new_text)

    def test_update_improvement_section(self):
        """Test updating improvement plan section"""
        self.service.initialise_survey(
            user=self.admin, project=self.project, survey=self.survey
        )
        self.service.update_consent_demography_config(
            user=self.admin,
            survey=self.survey,
            consent_config=self.survey.consent_config_default,
            demography_config=self.survey.demography_config_default,
            survey_body_path="Nurses",
        )

        improvement_section = self.survey.improvement_plan_sections.first()
        self.assertIsNotNone(improvement_section)

        new_plan = "This is an updated improvement plan"
        self.service.update_improvement_section(
            user=self.admin,
            survey=self.survey,
            improve_section=improvement_section,
            text=new_plan,
        )

        improvement_section.refresh_from_db()
        self.assertEqual(improvement_section.plan, new_plan)

    def test_get_survey_from_token_with_invalid_token(self):
        """Test that invalid token raises exception"""
        from survey.services.survey import InvalidInviteTokenException

        with self.assertRaises(InvalidInviteTokenException):
            self.service.get_survey_from_token(token="invalid_token_123")

    def test_get_survey_from_token_with_used_token(self):
        """Test that used token raises exception"""
        from survey.services.survey import InvalidInviteTokenException

        token = self.survey.current_invite_token()
        invitation = Invitation.objects.get(token=token)
        invitation.used = True
        invitation.save()

        with self.assertRaises(InvalidInviteTokenException):
            self.service.get_survey_from_token(token=token)

    def test_export_excel(self):
        """Test exporting survey to Excel format"""
        self.service.initialise_survey(
            user=self.admin, project=self.project, survey=self.survey
        )
        excel_data = self.service.export_excel(user=self.admin, survey=self.survey)
        self.assertIsNotNone(excel_data)

    def test_export_csv_unauthorized(self):
        """Test that unauthorized user cannot export CSV"""
        self.service.initialise_survey(
            user=self.admin, project=self.project, survey=self.survey
        )

        with self.assertRaises(django.core.exceptions.PermissionDenied):
            self.service.export_csv(user=self.anonymous_user, survey=self.survey)

    def test_export_excel_unauthorized(self):
        """Test that unauthorized user cannot export Excel"""
        self.service.initialise_survey(
            user=self.admin, project=self.project, survey=self.survey
        )

        with self.assertRaises(django.core.exceptions.PermissionDenied):
            self.service.export_excel(user=self.anonymous_user, survey=self.survey)

    def test_update_evidence_section_unauthorized(self):
        """Test that unauthorized user cannot update evidence section"""
        self.service.initialise_survey(
            user=self.admin, project=self.project, survey=self.survey
        )
        self.service.update_consent_demography_config(
            user=self.admin,
            survey=self.survey,
            consent_config=self.survey.consent_config_default,
            demography_config=self.survey.demography_config_default,
            survey_body_path="Nurses",
        )

        evidence_section = self.survey.evidence_sections.first()

        with self.assertRaises(django.core.exceptions.PermissionDenied):
            self.service.update_evidence_section(
                user=self.anonymous_user,
                survey=self.survey,
                evidence_section=evidence_section,
                text="Unauthorized text",
            )

    def test_update_improvement_section_unauthorized(self):
        """Test that unauthorized user cannot update improvement section"""
        self.service.initialise_survey(
            user=self.admin, project=self.project, survey=self.survey
        )
        self.service.update_consent_demography_config(
            user=self.admin,
            survey=self.survey,
            consent_config=self.survey.consent_config_default,
            demography_config=self.survey.demography_config_default,
            survey_body_path="Nurses",
        )

        improvement_section = self.survey.improvement_plan_sections.first()

        with self.assertRaises(django.core.exceptions.PermissionDenied):
            self.service.update_improvement_section(
                user=self.anonymous_user,
                survey=self.survey,
                improve_section=improvement_section,
                text="Unauthorized plan",
            )

    def test_get_user_role_with_anonymous_user(self):
        """Test get_user_role with anonymous user returns None"""
        from django.contrib.auth.models import AnonymousUser

        anon = AnonymousUser()
        role = self.service.get_user_role(user=anon, survey=self.survey)
        self.assertIsNone(role)

    def test_can_create_with_project(self):
        """Test can_create checks permission on project"""
        self.assertTrue(self.service.can_create(self.admin, self.project))
        self.assertFalse(self.service.can_create(self.anonymous_user, self.project))

    def test_accept_response_creates_survey_response(self):
        """Test that accept_response creates a SurveyResponse object"""
        response_data = json.dumps({"field1": "value1", "field2": "value2"})

        initial_count = SurveyResponse.objects.filter(survey=self.survey).count()

        self.service.accept_response(survey=self.survey, responseValues=response_data)

        final_count = SurveyResponse.objects.filter(survey=self.survey).count()
        self.assertEqual(final_count, initial_count + 1)

        # Check the response was stored correctly
        response = SurveyResponse.objects.filter(survey=self.survey).latest("id")
        self.assertEqual(response.answers, response_data)

    def test_generate_mock_responses_superuser_only(self):
        """Test that only superuser can generate mock responses"""
        with self.assertRaises(django.core.exceptions.PermissionDenied):
            self.service.generate_mock_responses(
                user=self.admin, survey=self.survey, num_responses=5
            )

    def test_create_invitation_invalidates_old_tokens(self):
        """Test that creating new invitation invalidates all old ones"""
        # Create multiple invitations
        inv1 = self.service.create_invitation(user=self.admin, survey=self.survey)
        inv2 = self.service.create_invitation(user=self.admin, survey=self.survey)
        inv3 = self.service.create_invitation(user=self.admin, survey=self.survey)

        # Refresh from DB
        inv1.refresh_from_db()
        inv2.refresh_from_db()

        # Old invitations should be marked as used
        self.assertTrue(inv1.used)
        self.assertTrue(inv2.used)

        # Latest invitation should not be used
        self.assertFalse(inv3.used)

    def test_initialise_survey_sets_config(self):
        """Test that initialise_survey sets survey configuration"""
        self.assertIsNone(self.survey.survey_config)

        self.service.initialise_survey(
            user=self.admin, project=self.project, survey=self.survey
        )

        self.survey.refresh_from_db()
        self.assertIsNotNone(self.survey.survey_config)
        self.assertIsInstance(self.survey.survey_config, dict)

    def test_duplicate_survey_copies_all_fields(self):
        """Test that duplicate_survey copies all relevant fields"""
        # Properly initialise the survey
        self.service.initialise_survey(self.admin, self.project, self.survey)
        self.service.update_consent_demography_config(
            self.admin,
            self.survey,
            demography_config=self.survey.demography_config_default,
            survey_body_path=self.survey.survey_body_path,
            consent_config=self.survey.consent_config_default,
        )

        original_description = "Original description"
        self.survey.description = original_description
        self.survey.save()

        duplicated = self.service.duplicate_survey(user=self.admin, survey=self.survey)

        # Check fields are copied
        self.assertEqual(duplicated.description, original_description)
        self.assertEqual(duplicated.project, self.survey.project)
        self.assertEqual(duplicated.survey_body_path, self.survey.survey_body_path)

    def test_initialise_survey_unauthorized(self):
        """Test that unauthorized user cannot initialise survey"""
        with self.assertRaises(django.core.exceptions.PermissionDenied):
            self.service.initialise_survey(
                user=self.anonymous_user, project=self.project, survey=self.survey
            )
