"""
Form for adding existing users to an organisation
"""

import django.forms as forms
from django.core.exceptions import ValidationError

from home.constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER
from home.models import OrganisationMembership, User


class AddExistingMemberForm(forms.Form):
    """
    Form for adding an existing user to an organisation.
    This is idempotent - it won't fail if the user is already a member.
    """

    email = forms.EmailField(
        label="Email address of existing user",
        help_text="Enter the email address of a user who already has an account",
        widget=forms.EmailInput(attrs={"placeholder": "user@example.com"}),
    )

    def __init__(self, *args, **kwargs):
        self.organisation = kwargs.pop("organisation", None)
        self.requesting_user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data["email"]

        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError(
                f"No user with email address '{email}' exists. "
                "Please invite them to create an account first."
            )

        # Store the user for later use in save()
        self.user_to_add = user

        # Check if user is already a member (but don't fail - idempotent)
        if OrganisationMembership.objects.filter(
                user=user, organisation=self.organisation
        ).exists():
            # Store that this is a duplicate (we'll handle it gracefully)
            self.is_duplicate = True
        else:
            self.is_duplicate = False

        return email

    def get_user(self):
        """Return the user object after validation"""
        if hasattr(self, "user_to_add"):
            return self.user_to_add
        return None
