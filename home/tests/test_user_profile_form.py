"""
Test the UserProfileForm
"""

import django.test

from home.forms.user_profile import UserProfileForm
from SORT.test.model_factory import UserFactory


class UserProfileFormTestCase(django.test.TestCase):

    def setUp(self):
        self.user = UserFactory()
        self.other_user = UserFactory()

    def test_rejects_case_variant_duplicate_email(self):
        """
        Changing to an email that only differs in case from another user's
        should be rejected as a duplicate (issue #667).
        """
        form = UserProfileForm(
            data={
                "email": self.other_user.email.upper(),
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
            },
            instance=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
