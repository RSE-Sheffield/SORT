import csv
import json
import logging
import random
from io import StringIO
from typing import Any

from django.shortcuts import get_object_or_404

from home.models import Project, User
from home.services import BasePermissionService
from survey.models import Invitation, Survey, SurveyResponse

logger = logging.getLogger(__name__)


class InvalidInviteTokenException(Exception):
    pass


class SurveyService(BasePermissionService):

    def can_view(self, user: User, instance: Any) -> bool:
        return True

    def can_create(self, user: User) -> bool:
        # TODO: Requires checking that project
        return True

    def can_edit(self, user: User, instance: Any) -> bool:
        return True

    def can_delete(self, user: User, instance: Any) -> bool:
        return True

    def get_survey(self, survey_id: int) -> Survey:
        survey = get_object_or_404(Survey, pk=survey_id)
        return survey

    def create_survey(self, survey: Survey, project: Project) -> Survey:
        survey.project = project

        # TODO: Make a proper loader function
        with open("data/survey_config/consent_only_config.json") as f:
            consent_config = json.load(f)
            survey.consent_config = consent_config

        with open("data/survey_config/demography_only_config.json") as f:
            demo_config = json.load(f)
            survey.demography_config = demo_config

        survey.survey_config = dict(sections=list())
        survey.save()

        return survey

    def update_consent_demography_config(
            self, survey: Survey, consent_config, demography_config
    ) -> Survey:
        survey.consent_config = consent_config
        survey.demography_config = demography_config

        with open("data/survey_config/sort_only_config.json") as f:
            sort_config = json.load(f)
            merged_sections = (
                    survey.consent_config["sections"]
                    + sort_config["sections"]
                    + survey.demography_config["sections"]
            )
            survey.survey_config = {"sections": merged_sections}
        survey.save()
        return survey

    def get_survey_from_token(self, token: str) -> Survey:
        invitations = Invitation.objects.filter(token=token)

        # Checks that token is valid
        if not invitations.exists():
            logger.warning("Trying to get token that does not exist")
            raise InvalidInviteTokenException("Token does not exist")

        invitation = invitations.first()
        if invitation.used is True:
            logger.warning("Trying to use an invalid token")
            raise InvalidInviteTokenException("Token is invalid")

        return invitation.survey

    def accept_response(self, survey: Survey, responseValues):
        SurveyResponse.objects.create(survey=survey, answers=responseValues)

    def create_invitation(self, survey: Survey) -> Invitation:

        # Invalidate all other invite tokens
        for invite in survey.invitation_set.all():
            invite.used = True
            invite.save()

        # Add new invite token
        return Invitation.objects.create(survey=survey)

    def export_csv(self, survey: Survey) -> str:
        """
        Flatten the survey form to export as CSV
        Section titles are skipped
        Likert sublabels are expanded into individual columns
        """
        survey_config = survey.survey_config

        with StringIO() as f:
            writer = csv.writer(f)

            # Header
            header_fields = []
            for sIndex, section in enumerate(survey_config["sections"]):
                for fIndex, field in enumerate(section["fields"]):
                    if field["type"] == "likert":
                        for fsIndex, sublabel in enumerate(field["sublabels"]):
                            header_fields.append(sublabel)
                    else:
                        header_fields.append(field["label"])
            writer.writerow(header_fields)

            # Row values
            for response in survey.survey_response.all():
                answer = response.answers
                row_values = []
                for sIndex, section in enumerate(survey_config["sections"]):

                    if sIndex >= len(answer):
                        continue

                    for fIndex, field in enumerate(section["fields"]):
                        if fIndex >= len(answer[sIndex]):
                            continue

                        if field["type"] == "likert":
                            for fsIndex, sublabel in enumerate(field["sublabels"]):
                                row_values.append(answer[sIndex][fIndex][fsIndex])
                        else:
                            value = answer[sIndex][fIndex]
                            if isinstance(value, list):
                                row_values.append(",".join(value))
                            else:
                                row_values.append(value)

                writer.writerow(row_values)

            output_csv = f.getvalue()

        return output_csv

    def generate_mock_responses(self, survey: Survey, num_responses):
        """
        Generate a number of mock responses
        """
        for i in range(num_responses):
            self.accept_response(
                survey, responseValues=self.generate_mock_response(survey.survey_config)
            )

    def generate_mock_response(self, survey_config):
        output_data = []

        for section in survey_config["sections"]:
            section_data_output = []
            for field in section["fields"]:
                section_data_output.append(self.generate_random_field_value(field))

            output_data.append(section_data_output)

        return output_data

    def generate_random_field_value(self, field_config):
        type = field_config["type"]
        if type == "radio" or type == "select":
            # Pick one option
            num_options = len(field_config["options"])
            option_index = random.randint(0, num_options - 1)
            return str(field_config["options"][option_index])
        elif type == "checkbox":
            # Pick one random option
            num_options = len(field_config["options"])
            option_index = random.randint(0, num_options - 1)
            return [str(field_config["options"][option_index])]
        elif type == "likert":
            likert_output = []
            # Pick something
            for sublabel in field_config["sublabels"]:
                num_options = len(field_config["options"])
                option_index = random.randint(0, num_options - 1)
                likert_output.append(str(field_config["options"][option_index]))
            return likert_output

        elif type == "text":
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
