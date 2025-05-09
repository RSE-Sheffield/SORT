from http import HTTPStatus

import SORT.test.test_case


class HomeViewTestCase(SORT.test.test_case.ViewTestCase):

    def test_welcome_page(self):
        self.get("home", login=True)

    def test_welcome_page_unauthorised(self):
        """
        Redirects welcome page to login page.
        """
        # Don't log in first. Expect redirect.
        self.get("home", login=False, expected_status_code=HTTPStatus.FOUND)
