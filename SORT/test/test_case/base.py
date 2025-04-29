import django.test

from ..model_factory import UserFactory, SuperUserFactory


class SORTTestCase(django.test.TestCase):
    """
    A test case for testing the SORT web application.
    """

    def setUp(self):
        self.user = UserFactory()
        self.superuser = SuperUserFactory()
