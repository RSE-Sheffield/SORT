"""
Test the custom User model / UserManager
"""

import django.contrib.auth
import django.test

User = django.contrib.auth.get_user_model()


class UserManagerTestCase(django.test.TestCase):

    def test_create_user_lowercases_email(self):
        """
        Mixed-case emails should be stored lowercase (issue #667).
        """
        user = User.objects.create_user(
            first_name="Test",
            last_name="User",
            email="Mixed.Case@Example.COM",
            password="password123",
        )
        self.assertEqual(user.email, "mixed.case@example.com")

    def test_get_by_natural_key_is_case_insensitive(self):
        """
        Looking up a user by email (used during login) should ignore case.
        """
        User.objects.create_user(
            first_name="Test",
            last_name="User",
            email="someone@example.com",
            password="password123",
        )
        self.assertEqual(
            User.objects.get_by_natural_key("SOMEONE@EXAMPLE.COM").email,
            "someone@example.com",
        )
