from django import forms
from django.core.validators import EmailValidator


class InvitationForm(forms.Form):
    email = forms.EmailField(label='Participant Email',
                             max_length=100,
                             required=True,
                             validators=[EmailValidator()])