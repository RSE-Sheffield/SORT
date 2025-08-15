import csv
import io
import json
import logging
import random
import itertools
import secrets
from typing import Generator, Iterable

from django.db import models
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone

from home.models import Project

logger = logging.getLogger(__name__)


class Survey(models.Model):
    """
    Represents a survey that will be sent out to a participant
    """

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    survey_config = models.JSONField(null=True)
    consent_config = models.JSONField(null=True)
    demography_config = models.JSONField(null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    survey_body_path = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Are responses being collected?",
        null=False,
    )

    def __str__(self):
        return self.name

    def initialise(self):
        """
        Load an "empty" survey configuration
        """

        # Consent questions
        with open("data/survey_config/consent_only_config.json") as file:
            self.consent_config = json.load(file)

        # Demographics questions
        with open("data/survey_config/demography_only_config.json") as file:
            self.demography_config = json.load(file)

        # No SORT questions by default
        self.survey_config = dict(sections=list())
        self.survey_body_path = "Nurses"

    def get_absolute_url(self):
        return reverse("survey", kwargs={"pk": self.pk})

    def current_invite_token(self):
        for invite in self.invitation_set.all():
            if not invite.is_expired() and not invite.used:
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
        return tuple(
            self.consent_config["sections"]
            + self.demography_config["sections"]
            + self.survey_config["sections"]
        )

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

    def responses_iter_values(self) -> Generator[str, None, None]:
        """
        Iterate over all responses, with the answers flattened to a row of data
        """
        # Iterate over survey response answer fields
        for answers in self.survey_response.all():
            yield answers.answers_values

    def responses_iter(self) -> Generator[dict[str, str], None, None]:
        """
        Generate an iterable of flat dictionaries, each with questions and answers for this survey.
        """
        for answers_values in self.responses_iter_values():
            yield dict(itertools.zip_longest(self.fields, answers_values))

    def to_csv(self, **kwargs) -> str:
        """
        Flatten the survey form to export as CSV.

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

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(days=7)
