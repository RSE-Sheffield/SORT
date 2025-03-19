from http import HTTPStatus

import django.test
import django.urls
from django.contrib.auth import get_user_model

from .constants import PASSWORD

User = get_user_model()


class HomeTestCase(django.test.TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            first_name='John',
            last_name='Smith',
            email='john.smith@sheffield.ac.uk',
            password=PASSWORD,
        )

    def login(self):
        self.assertTrue(self.client.login(username=self.user.email, password=PASSWORD))

    def test_welcome_page_login_redirect(self):
        """
        Redirects welcome page to login page.
        """
        # Don't log in first
        response = self.client.get(django.urls.reverse('home'))
        # Expect redirect
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_welcome_page(self):
        self.login()
        response = self.client.get(django.urls.reverse('home'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
