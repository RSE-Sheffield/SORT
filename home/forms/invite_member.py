from django import forms
from invitations.forms import InviteForm as BaseInviteForm

from ..constants import ROLE_PROJECT_MANAGER


class InviteMemberForm(BaseInviteForm):
    """
    Custom invite form that hides the role field and defaults to Project Manager.
    """

    role = forms.CharField(
        initial=ROLE_PROJECT_MANAGER,
        widget=forms.HiddenInput(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure role is always set to Project Manager
        if "role" not in self.initial:
            self.initial["role"] = ROLE_PROJECT_MANAGER
