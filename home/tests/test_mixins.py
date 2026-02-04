"""
Unit tests for home.mixins module
"""

from unittest.mock import Mock

from django.test import RequestFactory, TestCase
from django.views import View

from SORT.test.model_factory import OrganisationFactory, UserFactory
from home.mixins import OrganisationRequiredMixin


class DummyViewWithMixin(OrganisationRequiredMixin, View):
    """Dummy view class for testing the mixin"""

    def get(self, request, *args, **kwargs):
        return Mock(status_code=200)


class OrganisationRequiredMixinTestCase(TestCase):
    """Tests for OrganisationRequiredMixin"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user_with_org = UserFactory()
        self.organisation = OrganisationFactory()
        self.organisation.members.add(self.user_with_org)

        self.user_without_org = UserFactory()

        self.view = DummyViewWithMixin.as_view()

    def test_dispatch_with_organisation_allows_access(self):
        """Test that users with an organisation can access the view"""
        request = self.factory.get("/")
        request.user = self.user_with_org

        response = self.view(request)
        self.assertEqual(response.status_code, 200)

    def test_dispatch_without_organisation_redirects(self):
        """Test that users without an organisation are redirected"""
        request = self.factory.get("/")
        request.user = self.user_without_org

        response = self.view(request)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith("organisation_create"))

    def test_user_with_multiple_organisations(self):
        """Test that users with multiple organisations can access"""
        # Add user to another organisation
        org2 = OrganisationFactory()
        org2.members.add(self.user_with_org)

        request = self.factory.get("/")
        request.user = self.user_with_org

        # User should still have access
        response = self.view(request)
        self.assertEqual(response.status_code, 200)

    def test_redirect_url_is_correct(self):
        """Test that redirect goes to organisation_create"""
        request = self.factory.get("/")
        request.user = self.user_without_org

        response = self.view(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn("organisation_create", response.url)

    def test_organisation_count_check(self):
        """Test that the mixin checks organisation count correctly"""
        request = self.factory.get("/")

        # User with org should have count > 0
        request.user = self.user_with_org
        self.assertGreater(request.user.organisation_set.count(), 0)

        # User without org should have count == 0
        request.user = self.user_without_org
        self.assertEqual(request.user.organisation_set.count(), 0)

    def test_dispatch_preserves_args_and_kwargs(self):
        """Test that dispatch passes args and kwargs correctly"""

        class TrackingView(OrganisationRequiredMixin, View):
            received_args = None
            received_kwargs = None

            def get(self, request, *args, **kwargs):
                self.received_args = args
                self.received_kwargs = kwargs
                return Mock(status_code=200)

        tracking_view = TrackingView()
        request = self.factory.get("/")
        request.user = self.user_with_org

        test_args = ("arg1", "arg2")
        test_kwargs = {"key1": "value1", "key2": "value2"}

        tracking_view.setup(request, *test_args, **test_kwargs)
        response = tracking_view.dispatch(request, *test_args, **test_kwargs)

        self.assertEqual(tracking_view.received_args, test_args)
        self.assertEqual(tracking_view.received_kwargs, test_kwargs)

    def test_user_removed_from_organisation(self):
        """Test that users removed from all organisations are redirected"""
        request = self.factory.get("/")
        request.user = self.user_with_org

        # Initially should have access
        response = self.view(request)
        self.assertEqual(response.status_code, 200)

        # Remove user from organisation
        self.organisation.members.remove(self.user_with_org)

        # Now should be redirected
        response = self.view(request)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith("organisation_create"))

    def test_organisation_count_exactly_one(self):
        """Test edge case with exactly one organisation"""
        request = self.factory.get("/")
        request.user = self.user_with_org

        # Should have exactly 1 organisation
        self.assertEqual(request.user.organisation_set.count(), 1)

        # Should allow access
        response = self.view(request)
        self.assertEqual(response.status_code, 200)
