"""
Form for requesting to join an existing organisation
"""

import django.forms as forms


class JoinRequestForm(forms.Form):
    """
    Optional note from a user asking to join an organisation, shown to that
    organisation's administrators so they can recognise the requester.
    """

    message = forms.CharField(
        label="Message to the organisation's administrators (optional)",
        help_text=(
            "For example your job title and team. This helps administrators "
            "recognise you and decide whether to approve your request."
        ),
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
