from django import forms
from django.forms import BaseFormSet, formset_factory
from strenum import StrEnum

from .validators.email_list_validator import EmailListValidator

from .models import Survey, Profession


class InvitationForm(forms.Form):
    email = forms.CharField(
        label="Participant Emails",
        help_text="Please enter a list of email addresses",
        required=True,
        validators=[EmailListValidator()],
        widget=forms.Textarea(attrs=dict(rows=6)),
    )
    message = forms.CharField(
        label="Message",
        help_text="(Optional) Additional message for the participants",
        required=False,
        widget=forms.Textarea(attrs=dict(rows=3)),
    )


class FormFieldType(StrEnum):
    CHAR = "char"
    TEXT = "text"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    LIKERT = "likert"


def create_field_from_config(field_config: dict):
    """
    Convert a field configuration into the correct django field
    """
    if field_config["type"] == FormFieldType.CHAR:
        field = forms.CharField(label=field_config["label"])
    elif field_config["type"] == FormFieldType.TEXT:
        field = forms.CharField(label=field_config["label"], widget=forms.Textarea)
    elif field_config["type"] == FormFieldType.RADIO:
        field = forms.ChoiceField(
            label=field_config["label"],
            choices=field_config["options"],
            widget=forms.RadioSelect,
        )
    elif field_config["type"] == FormFieldType.CHECKBOX:
        field = forms.MultipleChoiceField(
            label=field_config["label"],
            widget=forms.CheckboxSelectMultiple,
            choices=field_config["options"],
        )
    else:
        field = forms.CharField(label=field_config["label"], widget=forms.Textarea)

    if "required" in field_config:
        field.required = field_config["required"]

    return field


def create_dynamic_formset(field_configs: list):
    """
    Create a dynamic form set from a list of field configurations.
    """

    class BlankDynamicForm(forms.Form):
        pass

    class BaseTestFormSet(BaseFormSet):
        def add_fields(self, form, index):
            super().add_fields(form, index)
            for field_config in field_configs:
                form.fields[field_config["name"]] = create_field_from_config(
                    field_config
                )

    return formset_factory(BlankDynamicForm, BaseTestFormSet, min_num=1, max_num=1)


class SurveyCreateForm(forms.ModelForm):
    survey_body_path = forms.ChoiceField(
        label="Target audience",
        choices=Profession,
        help_text="Respondent profession",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    research_data_consent = forms.BooleanField(
        required=False,
        label="Allow research data sharing with the University of Sheffield",
        help_text=(
            "When enabled, anonymised survey response data may be shared with researchers at the "
            "University of Sheffield for studies of organisational research capacity. This requires "
            "both your consent here and each participant's individual consent when they submit their response. "
            "Shared data is extracted periodically, anonymised, and stored separately from this application. "
            "As responses are anonymous by default, individual responses cannot be identified or removed, "
            "though all data for an organisation, project, or survey can be removed on request."
        ),
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = Survey
        fields = ["name", "description", "survey_body_path"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }
