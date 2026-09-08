from http import HTTPStatus

from django.urls import reverse

import SORT.test.test_case


class LandingViewTestCase(SORT.test.test_case.ViewTestCase):

    def test_landing_page_anonymous(self):
        """
        Landing page should be accessible to anonymous users.
        """
        self.get("landing", login=False)

    def test_landing_page_authenticated_redirects(self):
        """
        Authenticated users should be redirected to dashboard.
        """
        self.get("landing", login=True, expected_status_code=HTTPStatus.FOUND)


class HomeViewTestCase(SORT.test.test_case.ViewTestCase):

    def test_dashboard_page(self):
        """
        Dashboard page (home) should be accessible to authenticated users.
        """
        self.get("dashboard", login=True)

    def test_dashboard_page_unauthorised(self):
        """
        Redirects dashboard page to login page for anonymous users.
        """
        # Don't log in first. Expect redirect.
        self.get("dashboard", login=False, expected_status_code=HTTPStatus.FOUND)

    def test_home_alias_backwards_compatibility(self):
        """
        Home URL should work as an alias to dashboard for backwards compatibility.
        """
        self.get("home", login=True)

    def test_dashboard_points_a_user_with_no_organisation_at_get_started(self):
        """
        The dashboard must offer a route out of the no-organisation state; the
        join-or-create choice itself belongs to organisation_get_started.
        """
        self.assertEqual(self.user.organisation_set.count(), 0)

        response = self.get("dashboard", login=True)

        self.assertContains(response, reverse("organisation_get_started"))
