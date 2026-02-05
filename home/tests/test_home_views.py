from http import HTTPStatus

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
