from django.test import TestCase
import django.test
from django.test import TestCase


class InviteTestCase(TestCase):
    def setUp(self):
        self.client = django.test.Client()

    def test_home_view(self):
        """
        Send out invitation page.
        """
        self.client.get('/invite/')
