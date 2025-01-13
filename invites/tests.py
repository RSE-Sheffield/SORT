import django.test


class InviteTestCase(django.test.TestCase):

    def test_invite_page(self):
        """
        Send out invitation page.
        """
        self.client.get("/invite/")
