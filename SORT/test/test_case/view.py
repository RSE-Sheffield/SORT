"""
A unit testing class for testing Django views.
"""

from http import HTTPStatus

import django.contrib.auth
import django.test
import django.urls

from SORT.test.model_factory import UserFactory, SuperUserFactory
from SORT.test.model_factory.user.constants import PASSWORD

User = django.contrib.auth.get_user_model()


class ViewTestCase(django.test.TestCase):
    """
    A test case for loading views using the Django test client.
    """

    def setUp(self):
        self.user = UserFactory()
        self.superuser = SuperUserFactory()

    def login(self):
        """
        Authenticate as a user.
        """
        self.assertTrue(self.client.login(username=self.user.email, password=PASSWORD),
                        "Authentication failed")

    def login_superuser(self):
        """
        Authenticate as a superuser.
        """
        self.assertTrue(
            self.client.login(
                username=self.superuser.email,
                password=PASSWORD,
            ), "Authentication failed"
        )

    def get(
            self,
            view_name: str,
            expected_status_code: int = HTTPStatus.OK,
            login: bool = True,
            **kwargs
    ):
        """
        Helper method to make a GET request to one of the views in this app.

        :param view_name: The name of the view as defined in urls.py
        :param expected_status_code: The HTTP status code that should be returned
        :param login: Whether to authenticate as a user before requesting the URL.
        :param kwargs: Additional arguments to pass to the GET request
        """
        if login:
            self.login()
        response = self.client.get(django.urls.reverse(view_name, kwargs=kwargs))
        self.assertEqual(response.status_code, expected_status_code)
        return response

    def post(
            self,
            view_name: str,
            expected_status_code: int = HTTPStatus.OK,
            login: bool = True,
            **kwargs
    ):
        """
        Helper method to make a POST request to one of the views in this app.

        :param view_name: The name of the view as defined in urls.py
        :param expected_status_code: The HTTP status code that should be returned
        :param login: Whether to authenticate as a user before requesting the URL.
        :param kwargs: Additional arguments to pass to the GET request
        """
        if login:
            self.login()
        response = self.client.post(django.urls.reverse(view_name, kwargs=kwargs))
        self.assertEqual(response.status_code, expected_status_code)
        return response
