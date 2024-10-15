from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

class ManagerSignupForm(UserCreationForm):
    confirm_manager = forms.BooleanField(
        label="I confirm that I am signing up as a manager.",
        required=True,
        error_messages={'required': 'You must confirm you are a manager to sign up.'}
    )

    def clean_confirm_manager(self):
        confirmed = self.cleaned_data.get('confirm_manager')
        if not confirmed:
            raise ValidationError("You must confirm that you are signing up as a manager.")
        return confirmed