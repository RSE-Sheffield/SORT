import django.contrib.auth.models
import django.forms as forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from invitations.models import Invitation

from home.services import organisation_service
from home.models import Organisation

User = django.contrib.auth.get_user_model()

organisation_service =


class ManagerSignupForm(UserCreationForm):
    """
    A form to register a new user (a new manager) who was invited by
    an existing manager of an organisation.
    """

    class Meta:
        model = User
        fields = ("password1", "password2")

    # Secret key for the invitation (hidden form field)
    key = forms.CharField(required=False, disabled=True, widget=forms.HiddenInput, label="")

    @property
    def invitation(self) -> Invitation:
        """
        The invitation that the existing manager send to the new user.
        """
        return Invitation.objects.get(key=self.data["key"])

    @property
    def inviter(self) -> User:
        """
        The user (manager) who invited this new manager.
        """
        return User.objects.get(pk=self.invitation.inviter_id)

    @property
    def organisation(self):
        """
        The organisation that the new user was invited to join.
        """
        return organisation_service.get_user_organisation(user=self.inviter)

    @property
    def email(self) -> str:
        """
        The email address of the new user that received the invitation email.
        """
        return self.invitation.email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.email
        user.username = user.email
        if commit:
            user.save()

        # Add user to organisation
        organisation_service.add_user_to_organisation(user, self.organisation)

        return user
