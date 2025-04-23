import django.contrib.auth.models
import django.forms as forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

User = django.contrib.auth.get_user_model()


class ManagerSignupForm(UserCreationForm):
    email = forms.EmailField(
        required=True, label="Email", error_messages={"required": "Email is required."}
    )

    class Meta:
        model = User
        fields = ("email", "password1", "password2")

    def clean_email(self) -> str:
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.username = user.email
        if commit:
            user.save()
        return user
