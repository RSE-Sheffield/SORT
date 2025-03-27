from http import HTTPStatus

import django.test
import django.urls
from django.contrib.auth import get_user_model

import SORT.test.test_case

from .constants import PASSWORD

User = get_user_model()


class HomeViewTestCase(SORT.test.test_case.ViewTestCase):

    def test_welcome_page(self):
        self.get("home", login=True)

    def test_welcome_page_unauthorised(self):
        """
        Redirects welcome page to login page.
        """
        # Don't log in first. Expect redirect.
        self.get("home", login=False, expected_status_code=HTTPStatus.FOUND)
