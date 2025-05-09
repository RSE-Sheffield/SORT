import django.forms as forms
from django.contrib.auth.forms import AuthenticationForm


class ManagerLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email", max_length=60, widget=forms.EmailInput(attrs={"autofocus": True})
    )
