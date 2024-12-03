from django import forms
from django.forms import BaseFormSet, formset_factory
from strenum import StrEnum
from django.core.validators import EmailValidator

class InvitationForm(forms.Form):
    email = forms.EmailField(label='Participant Email',
                             max_length=100,
                             required=True,
                             validators=[EmailValidator()])

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
    if field_config['type'] == FormFieldType.CHAR:
        field = forms.CharField(label=field_config["label"])
    elif field_config['type'] == FormFieldType.TEXT:
        field = forms.CharField(label=field_config["label"],
                                widget=forms.Textarea)
    elif field_config['type'] == FormFieldType.RADIO:
        field = forms.ChoiceField(label=field_config["label"],
                                  choices=field_config["options"],
                                  widget=forms.RadioSelect)
    elif field_config['type'] == FormFieldType.CHECKBOX:
        field = forms.MultipleChoiceField(label=field_config["label"],
                                          widget=forms.CheckboxSelectMultiple,
                                          choices=field_config["options"])
    else:
        field = forms.CharField(label=field_config["label"],
                                widget=forms.Textarea)

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
                form.fields[field_config["name"]] = create_field_from_config(field_config)

    return formset_factory(BlankDynamicForm, BaseTestFormSet, min_num=1, max_num=1)
