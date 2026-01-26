import csv
import io
import json
import logging
import random
import itertools
import secrets
import tempfile
from pathlib import Path
from typing import Generator, ContextManager
from contextlib import contextmanager

import xlsxwriter

from django.conf import settings
from django.db import models
from django.http import HttpRequest
from django.urls import reverse
import django.core.validators

from home.models import Project

logger = logging.getLogger(__name__)


class Profession(models.TextChoices):
    """
    Respondent job category for the target audience that will complete the survey.
    """

    NMAHPS = "NMAHPs", "Nurses, Midwives and Allied Health Professionals (NMAHPs)"
    NURSES = "Nurses", "Nurses"
    WIDMIVES = "Midwives", "Midwives"
    AHP = "AHP", "Allied Health Professionals (AHP)"


class Survey(models.Model):
    """
    Represents a survey that will be sent out to a participant
    """

    name = models.CharField(max_length=200, help_text="Survey title")
    description = models.TextField(blank=True, null=True)
    survey_config = models.JSONField(null=True)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, null=True, related_name="survey"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    survey_body_path = models.TextField(
        blank=False,
        null=False,
        default=Profession.NMAHPS,
        help_text="Respondent profession",
        choices=Profession,
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Are responses being collected?",
        null=False,
    )
    is_shared = models.BooleanField(
        verbose_name="Confirm data sharing agreement",
        default=True,
        help_text="Do you accept the terms of the data sharing agreement"
                  "between your organisation and the University of Sheffield?",
        null=False,
    )

    def __str__(self):
        return self.name

    @property
    def organisation(self):
        return self.project.organisation

    @property
    def consent_config_path(self) -> Path:
        """The location of the consent configuration file."""
        return Path(settings.SURVEY_TEMPLATE_DIR).joinpath(settings.CONSENT_TEMPLATE)

    @property
    def demography_config_filename(self) -> str:
        """
        The filename of the demographics questions configuration file for this profession.
        """
        return settings.DEMOGRAPHY_TEMPLATES[self.survey_body_path]

    @property
    def demography_config_path(self) -> Path:
        """
        The location of the demographics questions configuration file for this profession
        """
        return Path(settings.SURVEY_TEMPLATE_DIR) / self.demography_config_filename

    @property
    def consent_config_default(self) -> dict:
        """
        Survey consent question configuration
        """
        with self.consent_config_path.open() as file:
            return json.load(file)

    @property
    def consent_config(self) -> dict:
        """
        This survey's welcome/consent question configuration.
        """
        # Get the first section
        return dict(sections=[self.survey_config["sections"][0]])

    @property
    def demography_config(self) -> dict:
        """
        This survey's demographics question configuration.
        """
        # Get the final section
        return dict(sections=[self.survey_config["sections"][-1]])

    @property
    def demography_config_default(self) -> dict:
        """
        The default demographics questions configuration
        """
        with self.demography_config_path.open() as file:
            return json.load(file)

    def initialise(self):
        """
        Set up a new survey, populating the question sections.
        """
        self.reset()

    def get_absolute_url(self):
        return reverse("survey", kwargs={"pk": self.pk})

    def current_invite_token(self):
        for invite in self.invitation_set.all():
            if not invite.used:
                return invite.token
        return None

    def get_invite_link(self, request: HttpRequest):
        token = self.current_invite_token()
        if token is not None:
            return request.build_absolute_uri("/survey_response/" + token)

        return None

    @property
    def reference_number(self) -> str:
        """
        Unique identifier e.g. "SURVEY-000001"
        """
        return f"{self.__class__.__name__.upper()}-{str(self.pk).zfill(6)}"

    def generate_mock_responses(self, num_responses: int = 10):
        for _ in range(num_responses):
            self.accept_response(self._generate_mock_response())

    def _generate_mock_response(self):
        """
        Generate a dummy survey submission based on the questions in this survey.
        """
        output_data = list()

        for section in self.sections:
            section_data_output = list()
            for field in section["fields"]:
                section_data_output.append(self._generate_random_field_value(field))

            output_data.append(section_data_output)

        return output_data

    @property
    def sections(self) -> tuple[dict]:
        """
        The groups of questions in the survey.
        """
        # The consent_config and demography_config fields are redundant because their values are merged into the
        # survey_config field
        return tuple(self.survey_config["sections"])

    @classmethod
    def _generate_random_field_value(cls, field_config):
        field_type = field_config["type"]
        if field_type == "radio" or field_type == "select":
            # Pick one option
            num_options = len(field_config["options"])
            option_index = random.randint(0, num_options - 1)
            return str(field_config["options"][option_index])
        elif field_type == "checkbox":
            # Pick one random option
            num_options = len(field_config["options"])
            option_index = random.randint(0, num_options - 1)
            return [str(field_config["options"][option_index])]
        elif field_type == "likert":
            likert_output = list()
            # Pick something
            for _ in field_config["sublabels"]:
                num_options = len(field_config["options"])
                option_index = random.randint(0, num_options - 1)
                likert_output.append(str(field_config["options"][option_index]))
            return likert_output

        elif field_type == "text":
            if "textType" in field_config:
                if field_config["textType"] == "INTEGER_TEXT":
                    min_value = (
                        field_config["minNumValue"]
                        if "minNumValue" in field_config
                        else 0
                    )
                    max_value = (
                        field_config["maxNumValue"]
                        if "maxNumValue" in field_config
                        else 100
                    )
                    return str(random.randint(min_value, max_value))
                elif field_config["textType"] == "DECIMALS_TEXT":
                    min_value = (
                        field_config["minNumValue"]
                        if "minNumValue" in field_config
                        else 0
                    )
                    max_value = (
                        field_config["maxNumValue"]
                        if "maxNumValue" in field_config
                        else 100
                    )
                    return str(random.uniform(min_value, max_value))
                elif field_config["textType"] == "EMAIL_TEXT":
                    return "test@test.com"
                else:
                    return "Test plaintext field"
        else:
            return f"Test string for textarea field {field_config['label']}"

    def accept_response(self, answers: list):
        """
        Enter a new survey submission.
        """
        survey_response = SurveyResponse.objects.create(survey=self, answers=answers)
        survey_response.save()
        return survey_response

    @property
    def responses_count(self) -> int:
        """
        The number of submitted questionnaires.
        """
        return self.survey_response.count()

    @property
    def has_responses(self) -> bool:
        """
        Does this survey have any responses?
        """
        return self.survey_response.exists()

    def fields_iter(self) -> Generator[str, None, None]:
        """
        Iterate over all field (and sub-field) labels.
        """
        for section in self.sections:
            for field in section["fields"]:
                if field["type"] == "likert":
                    yield from field["sublabels"]
                else:
                    yield field["label"]

    @property
    def fields(self) -> tuple[str]:
        """
        Survey questions/field names
        """
        return tuple(self.fields_iter())

    def responses_iter_values(self):
        """
        Iterate over all responses, with the answers flattened to a row of data
        """
        # Iterate over survey response answer fields
        for survey_response in self.survey_response.all():
            yield survey_response.answers_values

    def responses_iter(self) -> Generator[dict[str, str], None, None]:
        """
        Generate an iterable of flat dictionaries, each with questions and answers for this survey.
        """
        for answers_values in self.responses_iter_values():
            yield dict(itertools.zip_longest(self.fields, answers_values))

    def to_csv(self, **kwargs) -> str:
        """
        Flatten the survey form to export as comma-separated values (CSV).

        :kwargs: Keyword arguments passed to csv.DictWriter
        :returns: CSV data
        """
        # Build text data
        with io.StringIO() as buffer:
            writer = csv.DictWriter(buffer, fieldnames=self.fields, **kwargs)
            writer.writeheader()
            # Iterate over survey responses, one line per submitted response
            for row in self.responses_iter():
                writer.writerow(row)
            return buffer.getvalue()

    @contextmanager
    def _to_excel(self) -> ContextManager[Path]:
        """
        Write survey responses to an Excel workbook file with a random name.

        :returns: The file name of a temporary Excel file
        """
        # Create a random filename (this will be deleted after the resource is used)
        path = Path(tempfile.mkdtemp()).joinpath("survey_responses.xlsx")

        # Create spreadsheet data
        workbook = xlsxwriter.Workbook(filename=path)
        sheet = workbook.add_worksheet(name=str(self))
        # Iterate over responses (one row per response)
        for i, row in enumerate(self.responses_iter()):
            # Write headers
            if i == 0:
                sheet.write_row(i, 0, row.keys())
            sheet.write_row(i + 1, 0, row.values())
        workbook.close()
        yield Path(workbook.filename)

        # Delete temporary file
        path.unlink()

    def to_excel(self) -> bytes:
        """
        Get the survey response data in Excel format.
        """
        with self._to_excel() as path:
            # Return data
            with path.open("rb") as file:
                return file.read()

    @property
    def template_filename(self) -> str:
        """
        The filename of the SORT questions config file for this profession e.g. "sort_only_config_midwives.json"
        """
        return settings.SURVEY_TEMPLATES[self.survey_body_path]

    @property
    def template_path(self) -> Path:
        """
        The location of the SORT questions configuration for this profession.
        """
        return settings.SURVEY_TEMPLATE_DIR.joinpath(self.template_filename)

    @property
    def sort_config(self) -> dict:
        """
        The SORT section configuration for this profession.
        """
        with self.template_path.open() as file:
            return json.load(file)

    def reset(self):
        """
        Reset all the questionnaire sections to their default values.
        """
        self.update(
            consent_config=self.consent_config_default,
            demography_config=self.demography_config_default,
        )

    def update(self, consent_config: dict, demography_config: dict):
        """
        Update the survey question configuration into the survey_config field.

        The consent and demographics fields may be overridden by the user, while the SORT questions are hard-coded.
        """
        self.survey_config = {
            # Merge sections by concatenating all questions
            "sections": consent_config["sections"]
            + self.sort_config["sections"]
            + demography_config["sections"]
        }


class SurveyEvidenceSection(models.Model):
    """
    Each part of each survey has a corresponding evidence section.

    The section_id always matches the section index in the survey.survey_config["sections"]
    """

    section_id = models.IntegerField(default=0)
    survey = models.ForeignKey(
        Survey, on_delete=models.CASCADE, related_name="evidence_sections"
    )
    title = models.TextField(blank=True, null=True)
    text = models.TextField(blank=True, null=True, default="No evidence provided.")

    class Meta:
        unique_together = [["survey", "section_id"]]
        indexes = [
            models.Index(fields=["section_id"]),
        ]


class SurveyImprovementPlanSection(models.Model):
    """
    The section_id always matches the section index in the survey.survey_config["sections"]
    """

    section_id = models.IntegerField(default=0, db_index=True)
    survey = models.ForeignKey(
        Survey, on_delete=models.CASCADE, related_name="improvement_sections"
    )
    title = models.TextField(blank=True, null=True)
    plan = models.TextField(blank=True, null=True)


def survey_file_upload_path(instance, filename):
    return f"survey/{instance.survey.pk}/{filename}"


class SurveyFile(models.Model):
    """
    A file attached to a survey.
    """

    file = models.FileField(upload_to=survey_file_upload_path, blank=True, null=True)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="files")


def evidence_file_upload_path(instance, filename):
    return f"survey_evidence/{instance.evidence_section.pk}/{filename}"


class SurveyEvidenceFile(models.Model):
    """
    An evidence file attached to a section of a survey.
    """

    file = models.FileField(upload_to=evidence_file_upload_path, blank=True, null=True)
    evidence_section = models.ForeignKey(
        SurveyEvidenceSection, on_delete=models.CASCADE, related_name="files"
    )


class SurveyResponse(models.Model):
    """
    Represents a single response to the survey from a participant
    """

    survey = models.ForeignKey(
        Survey, related_name="survey_response", on_delete=models.CASCADE
    )  # Many questions belong to one survey
    answers = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Survey {self.survey.pk} response {self.pk}"

    def get_absolute_url(self, token):
        return reverse("survey", kwargs={"pk": self.survey.pk})

    def clean(self):
        super().clean()

        # Paused survey
        if not self.survey.is_active:
            raise ValueError("Cannot submit response to an inactive survey")

    @property
    def answers_values(self) -> Generator[str, None, None]:
        """
        Build a flat iterable of all the answer values for this response.

        - Likert sub-labels are expanded into individual columns
        """
        for section in self.answers:
            for field in section:
                # Flatten sub-labels
                if isinstance(field, list):
                    yield from field
                else:
                    yield field


class Invitation(models.Model):
    """
    An invitation to submit a response to a survey.
    """

    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"Invitation for {self.survey.name}"

    def save(self, *args, **kwargs):
        if not self.token:
            # Try a new token until it doesn't clash with an existing one
            num_token_tries = 0
            max_token_tries = 50
            while num_token_tries < max_token_tries:
                token = secrets.token_urlsafe(32)
                if Invitation.objects.filter(token=token).count() < 1:
                    self.token = token
                    break
                num_token_tries += 1

        super().save(*args, **kwargs)

    @classmethod
    def recipient_list(cls, text: str) -> set[str]:
        """
        Parse email field into multiple email addresses.
        """
        # Replace delimiters with whitespace
        for delim in {",", ";", ":", "|"}:
            text = text.replace(delim, "\n")
        # Create a collection of email addresses
        email_addresses = set(text.split())
        # Check 'em
        for email in email_addresses:
            django.core.validators.validate_email(email)

        return email_addresses
