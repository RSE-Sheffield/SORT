import django.contrib.auth.models
import django.forms as forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from invitations.models import Invitation

User = django.contrib.auth.get_user_model()


class ManagerSignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("password1", "password2")

    # Secret key for the invitation (hidden form field)
    key = forms.CharField(required=False, disabled=True, widget=forms.HiddenInput, label="")

    @property
    def email(self) -> str:
        invitation = Invitation.objects.get(key=self.data["key"])
        return invitation.email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.email
        user.username = user.email
        if commit:
            user.save()
        return user
