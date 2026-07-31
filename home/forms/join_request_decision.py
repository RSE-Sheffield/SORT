"""
Forms for an organisation administrator deciding a join request
"""

import django.forms as forms

from home.constants import ROLE_PROJECT_MANAGER, ROLES


class JoinRequestApprovalForm(forms.Form):
    """
    Approve a join request, choosing the role to grant. Project Manager is
    pre-selected as the safer default; an administrator can promote the member
    afterwards.
    """

    role = forms.ChoiceField(
        label="Role",
        choices=ROLES,
        initial=ROLE_PROJECT_MANAGER,
        widget=forms.RadioSelect,
    )
    note = forms.CharField(
        label="Note to the requester (optional)",
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 2}),
    )


class JoinRequestRejectionForm(forms.Form):
    """
    Reject a join request. Deliberately has no role field, so a rejection can
    never accidentally consume one.
    """

    note = forms.CharField(
        label="Reason (optional, shared with the requester)",
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 2}),
    )
