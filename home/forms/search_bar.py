import django.forms as forms


class SearchBarForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Search...",
                "aria-label": "Search",
                "name": "q",
            }
        ),
    )
