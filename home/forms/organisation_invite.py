from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from invitations.forms import InviteForm
from invitations.adapters import get_invitations_adapter
from invitations.utils import get_invitation_model

Invitation = get_invitation_model()
User = get_user_model()


class OrganisationInviteForm(InviteForm):
    """
    Custom invite form that allows inviting existing users to organisations.

    Unlike the default InviteForm, this form permits inviting users who already
    have accounts on SORT, since a user may belong to multiple organisations.
    """

    def clean_email(self):
        """
        Validates email but allows existing users (unlike default behavior).
        Only prevents duplicate pending invitations or already-accepted invitations.
        """
        email = self.cleaned_data["email"]
        email = get_invitations_adapter().clean_email(email)

        errors = {
            "already_invited": _("This e-mail address has already been invited."),
            "already_accepted": _(
                "This e-mail address has already accepted an invite."
            ),
        }

        # Check for pending invitations
        if Invitation.objects.all_valid().filter(email__iexact=email, accepted=False):
            raise forms.ValidationError(errors["already_invited"])

        # Check for already-accepted invitations
        if Invitation.objects.filter(email__iexact=email, accepted=True):
            raise forms.ValidationError(errors["already_accepted"])

        # NOTE: We intentionally do NOT check if user exists
        # because we want to allow inviting existing users to new organisations

        return email
