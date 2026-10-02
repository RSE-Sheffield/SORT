"""
Unit tests for the invitation model.
"""

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from SORT.test.model_factory import SurveyFactory
from django.test import RequestFactory

from survey.models import Invitation, SHORT_CODE_ALPHABET, SHORT_CODE_LENGTH


class TestInvitationModel(TestCase):
    def setUp(self):
        self.survey = SurveyFactory()
        self.survey.initialise()
        self.survey.save()

    def test_invitation_creation(self):
        """Test that an invitation can be created successfully."""
        invitation = Invitation.objects.create(survey=self.survey)
        self.assertIsNotNone(invitation)
        self.assertEqual(invitation.survey, self.survey)
        self.assertFalse(invitation.used)
        self.assertIsNotNone(invitation.created_at)

    def test_invitation_str_representation(self):
        """Test the string representation of an invitation."""
        invitation = Invitation.objects.create(survey=self.survey)
        expected = f"Invitation for {self.survey.name}"
        self.assertEqual(str(invitation), expected)

    def test_token_auto_generation(self):
        """Test that a token is automatically generated when creating an invitation."""
        invitation = Invitation.objects.create(survey=self.survey)
        self.assertIsNotNone(invitation.token)
        self.assertTrue(len(invitation.token) > 0)
        self.assertEqual(len(invitation.token), 43)  # URL-safe base64 encoded 32 bytes

    def test_token_is_unique(self):
        """Test that tokens are unique across invitations."""
        invitation1 = Invitation.objects.create(survey=self.survey)
        invitation2 = Invitation.objects.create(survey=self.survey)
        self.assertNotEqual(invitation1.token, invitation2.token)

    def test_token_uniqueness_constraint(self):
        """Test that the database enforces token uniqueness."""
        invitation1 = Invitation.objects.create(survey=self.survey)
        invitation2 = Invitation(survey=self.survey, token=invitation1.token)
        with self.assertRaises(IntegrityError):
            invitation2.save()

    def test_token_not_editable(self):
        """Test that token field is not editable (field property)."""
        field = Invitation._meta.get_field('token')
        self.assertFalse(field.editable)

    def test_used_defaults_to_false(self):
        """Test that the 'used' field defaults to False."""
        invitation = Invitation.objects.create(survey=self.survey)
        self.assertFalse(invitation.used)

    def test_marking_invitation_as_used(self):
        """Test that an invitation can be marked as used."""
        invitation = Invitation.objects.create(survey=self.survey)
        invitation.used = True
        invitation.save()
        invitation.refresh_from_db()
        self.assertTrue(invitation.used)

    def test_multiple_invitations_per_survey(self):
        """Test that a survey can have multiple invitations."""
        invitation1 = Invitation.objects.create(survey=self.survey)
        invitation2 = Invitation.objects.create(survey=self.survey)
        invitation3 = Invitation.objects.create(survey=self.survey)

        invitations = Invitation.objects.filter(survey=self.survey)
        self.assertEqual(invitations.count(), 3)
        self.assertIn(invitation1, invitations)
        self.assertIn(invitation2, invitations)
        self.assertIn(invitation3, invitations)

    def test_cascade_delete_when_survey_deleted(self):
        """Test that invitations are deleted when their survey is deleted."""
        invitation = Invitation.objects.create(survey=self.survey)
        invitation_pk = invitation.pk
        self.survey.delete()

        with self.assertRaises(Invitation.DoesNotExist):
            Invitation.objects.get(pk=invitation_pk)

    def test_created_at_auto_populated(self):
        """Test that created_at is automatically populated."""
        before_creation = timezone.now()
        invitation = Invitation.objects.create(survey=self.survey)
        after_creation = timezone.now()

        self.assertIsNotNone(invitation.created_at)
        self.assertGreaterEqual(invitation.created_at, before_creation)
        self.assertLessEqual(invitation.created_at, after_creation)

    def test_recipient_list_single_email(self):
        """Test parsing a single email address."""
        result = Invitation.recipient_list("test@example.com")
        self.assertEqual(result, {"test@example.com"})

    def test_recipient_list_comma_separated(self):
        """Test parsing comma-separated email addresses."""
        result = Invitation.recipient_list("test1@example.com, test2@example.com, test3@example.com")
        self.assertEqual(result, {"test1@example.com", "test2@example.com", "test3@example.com"})

    def test_recipient_list_semicolon_separated(self):
        """Test parsing semicolon-separated email addresses."""
        result = Invitation.recipient_list("test1@example.com; test2@example.com")
        self.assertEqual(result, {"test1@example.com", "test2@example.com"})

    def test_recipient_list_colon_separated(self):
        """Test parsing colon-separated email addresses."""
        result = Invitation.recipient_list("test1@example.com: test2@example.com")
        self.assertEqual(result, {"test1@example.com", "test2@example.com"})

    def test_recipient_list_pipe_separated(self):
        """Test parsing pipe-separated email addresses."""
        result = Invitation.recipient_list("test1@example.com | test2@example.com")
        self.assertEqual(result, {"test1@example.com", "test2@example.com"})

    def test_recipient_list_mixed_delimiters(self):
        """Test parsing email addresses with mixed delimiters."""
        result = Invitation.recipient_list(
            "test1@example.com, test2@example.com; test3@example.com | test4@example.com")
        self.assertEqual(result, {"test1@example.com", "test2@example.com", "test3@example.com", "test4@example.com"})

    def test_recipient_list_newline_separated(self):
        """Test parsing newline-separated email addresses."""
        result = Invitation.recipient_list("test1@example.com\ntest2@example.com\ntest3@example.com")
        self.assertEqual(result, {"test1@example.com", "test2@example.com", "test3@example.com"})

    def test_recipient_list_whitespace_handling(self):
        """Test that extra whitespace is handled correctly."""
        result = Invitation.recipient_list("  test1@example.com   test2@example.com  ")
        self.assertEqual(result, {"test1@example.com", "test2@example.com"})

    def test_recipient_list_deduplication(self):
        """Test that duplicate email addresses are removed."""
        result = Invitation.recipient_list("test@example.com, test@example.com, test@example.com")
        self.assertEqual(result, {"test@example.com"})

    def test_recipient_list_invalid_email(self):
        """Test that invalid email addresses raise a validation error."""
        with self.assertRaises(ValidationError):
            Invitation.recipient_list("not-an-email")

    def test_recipient_list_invalid_email_in_list(self):
        """Test that a list with one invalid email raises a validation error."""
        with self.assertRaises(ValidationError):
            Invitation.recipient_list("test@example.com, not-an-email, another@example.com")

    def test_recipient_list_empty_string(self):
        """Test parsing an empty string."""
        result = Invitation.recipient_list("")
        self.assertEqual(result, set())

    def test_invitation_foreign_key_relationship(self):
        """Test the foreign key relationship between Invitation and Survey."""
        invitation = Invitation.objects.create(survey=self.survey)
        self.assertEqual(invitation.survey, self.survey)
        self.assertIn(invitation, self.survey.invitation_set.all())

    def test_token_max_length(self):
        """Test that the token field respects max_length constraint."""
        field = Invitation._meta.get_field('token')
        self.assertEqual(field.max_length, 64)

    def test_short_code_auto_generation(self):
        """Test that a short code is automatically generated using the unambiguous alphabet."""
        invitation = Invitation.objects.create(survey=self.survey)
        self.assertEqual(len(invitation.short_code), SHORT_CODE_LENGTH)
        self.assertTrue(set(invitation.short_code) <= set(SHORT_CODE_ALPHABET))

    def test_short_code_is_unique(self):
        """Test that short codes are unique across invitations."""
        codes = {Invitation.objects.create(survey=self.survey).short_code for _ in range(10)}
        self.assertEqual(len(codes), 10)

    def test_short_code_not_editable(self):
        field = Invitation._meta.get_field("short_code")
        self.assertFalse(field.editable)

    def test_invite_links(self):
        """Test that both the full and short invitation links are built for the current invitation."""
        invitation = Invitation.objects.create(survey=self.survey)
        request = RequestFactory().get("/")
        self.assertEqual(
            self.survey.get_invite_link(request),
            f"http://testserver/survey_response/{invitation.token}",
        )
        self.assertEqual(
            self.survey.get_short_invite_link(request),
            f"http://testserver/s/{invitation.short_code}",
        )

    def test_invite_links_none_without_invitation(self):
        request = RequestFactory().get("/")
        self.assertIsNone(self.survey.get_invite_link(request))
        self.assertIsNone(self.survey.get_short_invite_link(request))
