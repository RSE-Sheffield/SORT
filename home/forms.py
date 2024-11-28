from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()
class ManagerSignupForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email', error_messages={'required': 'Email is required.'})


    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = user.email
        if commit:
            user.save()
        return user


class ManagerLoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email', max_length=60, widget=forms.EmailInput(attrs={'autofocus': True}))

    class Meta:
        model = AuthenticationForm
        fields = ['username', 'password']


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'firstname', 'lastname', 'password']

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user