"""
Unit tests for survey.mixins module
"""

from unittest.mock import Mock

from django.test import RequestFactory, TestCase
from django.views import View

from SORT.test.model_factory import InvitationFactory
from survey.mixins import TokenAuthenticationMixin
from survey.models import Invitation


class DummyViewWithMixin(TokenAuthenticationMixin, View):
    """Dummy view class for testing the mixin"""

    def get(self, request, *args, **kwargs):
        return Mock(status_code=200)


class TokenAuthenticationMixinTestCase(TestCase):
    """Tests for TokenAuthenticationMixin"""

    def setUp(self):
        self.factory = RequestFactory()
        self.invitation = InvitationFactory()
        self.valid_token = self.invitation.token
        self.view = DummyViewWithMixin.as_view()

    def test_is_valid_token_with_valid_token(self):
        """Test that is_valid_token returns True for a valid token"""
        mixin = TokenAuthenticationMixin()
        self.assertTrue(mixin.is_valid_token(self.valid_token))

    def test_is_valid_token_with_invalid_token(self):
        """Test that is_valid_token returns False for an invalid token"""
        mixin = TokenAuthenticationMixin()
        invalid_token = "invalid_token_12345"
        self.assertFalse(mixin.is_valid_token(invalid_token))

    def test_is_valid_token_with_none(self):
        """Test that is_valid_token returns False for None"""
        mixin = TokenAuthenticationMixin()
        self.assertFalse(mixin.is_valid_token(None))

    def test_is_valid_token_with_empty_string(self):
        """Test that is_valid_token returns False for empty string"""
        mixin = TokenAuthenticationMixin()
        self.assertFalse(mixin.is_valid_token(""))

    def test_dispatch_with_valid_token(self):
        """Test that dispatch allows request with valid token"""
        request = self.factory.get("/")
        response = self.view(request, token=self.valid_token)
        self.assertEqual(response.status_code, 200)

    def test_dispatch_with_invalid_token_redirects(self):
        """Test that dispatch redirects when token is invalid"""
        request = self.factory.get("/")
        response = self.view(request, token="invalid_token")
        # Should redirect to error_page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith("error_page"))

    def test_dispatch_with_no_token_redirects(self):
        """Test that dispatch redirects when no token is provided"""
        request = self.factory.get("/")
        response = self.view(request, token=None)
        # Should redirect to error_page
        self.assertEqual(response.status_code, 302)

    def test_dispatch_with_empty_token_redirects(self):
        """Test that dispatch redirects when token is empty string"""
        request = self.factory.get("/")
        response = self.view(request, token="")
        # Should redirect to error_page
        self.assertEqual(response.status_code, 302)

    def test_multiple_invitations_same_token_check(self):
        """Test token validation when multiple invitations exist"""
        # Create another invitation
        invitation2 = InvitationFactory()

        mixin = TokenAuthenticationMixin()

        # Both tokens should be valid
        self.assertTrue(mixin.is_valid_token(self.valid_token))
        self.assertTrue(mixin.is_valid_token(invitation2.token))

        # Invalid token should still be invalid
        self.assertFalse(mixin.is_valid_token("nonexistent_token"))

    def test_is_valid_token_uses_database_query(self):
        """Test that is_valid_token queries the database correctly"""
        mixin = TokenAuthenticationMixin()

        # Count initial invitations
        initial_count = Invitation.objects.count()
        self.assertGreater(initial_count, 0)

        # Valid token should exist in database
        self.assertTrue(Invitation.objects.filter(token=self.valid_token).exists())
        self.assertTrue(mixin.is_valid_token(self.valid_token))

        # Invalid token should not exist in database
        invalid_token = "definitely_not_a_real_token"
        self.assertFalse(Invitation.objects.filter(token=invalid_token).exists())
        self.assertFalse(mixin.is_valid_token(invalid_token))

    def test_dispatch_calls_is_valid_token(self):
        """Test that dispatch method calls is_valid_token"""
        request = self.factory.get("/")

        # Create a custom view to track method calls
        class TrackingView(TokenAuthenticationMixin, View):
            is_valid_token_called = False
            token_checked = None

            def is_valid_token(self, token):
                self.is_valid_token_called = True
                self.token_checked = token
                return super().is_valid_token(token)

            def get(self, request, *args, **kwargs):
                return Mock(status_code=200)

        tracking_view = TrackingView()
        tracking_view.setup(request, token=self.valid_token)
        tracking_view.dispatch(request, token=self.valid_token)

        self.assertTrue(tracking_view.is_valid_token_called)
        self.assertEqual(tracking_view.token_checked, self.valid_token)

    def test_expired_invitation_token_still_valid_in_database(self):
        """Test that token validation only checks existence, not expiry"""
        # Mark invitation as used (expired)
        self.invitation.used = True
        self.invitation.save()

        mixin = TokenAuthenticationMixin()

        # Token should still be "valid" from database existence perspective
        # (The mixin only checks if token exists, not if it's used)
        self.assertTrue(Invitation.objects.filter(token=self.valid_token).exists())
        self.assertTrue(mixin.is_valid_token(self.valid_token))
