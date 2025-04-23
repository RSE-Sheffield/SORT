import django.forms
import django.contrib.auth

from home.models import OrganisationMembership

User = django.contrib.auth.get_user_model()


class OrganisationMembershipCreateForm(django.forms.ModelForm):
    class Meta:
        model = User
        fields = ["email"]
