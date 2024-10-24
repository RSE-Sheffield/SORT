from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

class ManagerSignupForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email', error_messages={'required': 'Email is required.'})
    confirm_manager = forms.BooleanField(
        label="I confirm that I am signing up as a manager.",
        required=True,
        error_messages={'required': 'You must confirm you are a manager to sign up.'}
    )

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2', 'confirm_manager')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def clean_confirm_manager(self):
        confirmed = self.cleaned_data.get('confirm_manager')
        if not confirmed:
            raise ValidationError("You must confirm that you are signing up as a manager.")
        return confirmed
