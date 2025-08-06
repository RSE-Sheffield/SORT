import csv
import json
import logging
from io import StringIO
from typing import Dict, Optional

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import UploadedFile
from django.core.files.uploadhandler import UploadFileException
from django.shortcuts import get_object_or_404

from home.constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER
from home.models import Project, User
from home.services import BasePermissionService, project_service
from home.services.base import requires_permission
from survey.models import (
    Invitation,
    Survey,
    SurveyEvidenceFile,
    SurveyEvidenceSection,
    SurveyFile,
    SurveyImprovementPlanSection,
    SurveyResponse,
)

logger = logging.getLogger(__name__)


class InvalidInviteTokenException(Exception):
    pass


class SurveyService(BasePermissionService):

    def get_user_role(self, user: User, survey: Survey) -> Optional[str]:
        """Get user's role in the project's organisation"""
        try:
            return survey.project.organisation.get_user_role(user)
        except (
                AttributeError
        ):  # In case user is AnonymousUser or organisation method fails
            return None

    def can_view(self, user: User, survey: Survey) -> bool:
        """Must be a member of the organisation the survey belongs to in order to view"""
        role = self.get_user_role(user, survey)
        return role in [ROLE_ADMIN, ROLE_PROJECT_MANAGER]

    def can_edit(self, user: User, survey: Survey) -> bool:
        """Must be a member of the organisation the survey belongs to in order to edit"""
        role = self.get_user_role(user, survey)
        return role in [ROLE_ADMIN, ROLE_PROJECT_MANAGER]

    def can_delete(self, user: User, survey: Survey) -> bool:
        """Must be a member of the organisation the survey belongs to in order to delete"""
        role = self.get_user_role(user, survey)
        return role in [ROLE_ADMIN, ROLE_PROJECT_MANAGER]

    def can_create(self, user: User, project: Project) -> bool:
        """Must be a member of the organisation the survey belongs to in order to delete"""
        role = project_service.get_user_role(user, project)
        return role in [ROLE_ADMIN, ROLE_PROJECT_MANAGER]

    def get_survey(self, user: User, survey_id: int) -> Survey:
        survey = get_object_or_404(Survey, pk=survey_id)
        if self.can_view(user, survey):
            return survey
        else:
            raise PermissionDenied("Not allowed to view the survey")

    @requires_permission("create", obj_param="project")
    def initialise_survey(self, user: User, project: Project, survey: Survey):

        survey.project = project

        # TODO: Make a proper loader function
        with open("data/survey_config/consent_only_config.json") as f:
            consent_config = json.load(f)
            survey.consent_config = consent_config

        with open("data/survey_config/demography_only_config.json") as f:
            demo_config = json.load(f)
            survey.demography_config = demo_config

        survey.survey_config = dict(sections=list())
        survey.survey_body_path = "Nurses"
        survey.save()

    @requires_permission("edit", obj_param="survey")
    def update_consent_demography_config(
            self,
            user: User,
            survey: Survey,
            consent_config,
            demography_config,
            survey_body_path,
    ) -> Survey:
        """
        Modify demographics fields on this survey
        """

        if survey.has_responses:
            raise PermissionDenied("Cannot modify survey with responses")

        survey.consent_config = consent_config
        survey.demography_config = demography_config
        survey.survey_body_path = survey_body_path

        body_path = "sort_only_config.json"
        if survey_body_path in settings.SURVEY_TEMPLATES:
            body_path = settings.SURVEY_TEMPLATES[survey_body_path]

        with open(settings.SURVEY_TEMPLATE_DIR / body_path) as f:
            sort_config = json.load(f)
            merged_sections = (
                    survey.consent_config["sections"]
                    + sort_config["sections"]
                    + survey.demography_config["sections"]
            )
            survey.survey_config = {"sections": merged_sections}

        survey.save()

        self._create_survey_evidence_sections(survey)
        self._create_survey_improvement_sections(survey)
        return survey

    @requires_permission("edit", obj_param="survey")
    def duplicate_survey(self, user: User, survey: Survey):
        new_survey = Survey.objects.create(
            project=survey.project,
            name=f"Copy of {survey.name}",
            description=survey.description,
        )

        self.update_consent_demography_config(
            user,
            new_survey,
            consent_config=survey.consent_config,
            demography_config=survey.demography_config,
            survey_body_path=survey.survey_body_path,
        )

        return new_survey

    def _create_survey_evidence_sections(
            self, survey: Survey, clear_existing_sections: bool = True
    ):
        if not survey.survey_config["sections"]:
            raise ValueError("No sections available")

        if clear_existing_sections:
            for evidence_section in SurveyEvidenceSection.objects.filter(survey=survey):
                evidence_section.delete()  # Delete all previous section first

        for section_index, section in enumerate(survey.survey_config["sections"]):
            if section["type"] == "sort":
                survey_evidence_section = SurveyEvidenceSection.objects.create(
                    survey=survey, section_id=section_index, title=section["title"]
                )
                survey_evidence_section.save()

    def _create_survey_improvement_sections(
            self, survey: Survey, clear_existing_sections: bool = True
    ):
        if clear_existing_sections:
            for improve_section in SurveyImprovementPlanSection.objects.filter(
                    survey=survey
            ):
                improve_section.delete()  # Delete all previous section first

        for section_index, section in enumerate(survey.survey_config["sections"]):
            if section["type"] == "sort":
                survey_improvement_plan_section = (
                    SurveyImprovementPlanSection.objects.create(
                        survey=survey, section_id=section_index, title=section["title"]
                    )
                )
                survey_improvement_plan_section.save()

    @requires_permission("edit", obj_param="survey")
    def update_evidence_section(
            self, user: User, survey: Survey, evidence_section: SurveyEvidenceSection, text
    ):
        evidence_section.text = text
        evidence_section.save()

    @requires_permission("edit", obj_param="survey")
    def update_improvement_section(
            self,
            user: User,
            survey: Survey,
            improve_section: SurveyImprovementPlanSection,
            text,
    ):
        improve_section.plan = text
        improve_section.save()

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

    @requires_permission("edit", obj_param="survey")
    def create_invitation(self, user: User, survey: Survey) -> Invitation:

        # Invalidate all other invite tokens
        for invite in survey.invitation_set.all():
            invite.used = True
            invite.save()

        # Add new invite token
        return Invitation.objects.create(survey=survey)

    @requires_permission("view", obj_param="survey")
    def export_csv(self, user: User, survey: Survey) -> str:
        return survey.to_csv()

    def _is_extension_supported(self, file_name: str) -> bool:
        for extension in settings.MEDIA_SUPPORTED_EXTENSIONS:
            if file_name.lower().endswith(extension):
                return True
        return False

    @requires_permission("edit", obj_param="survey")
    def add_uploaded_files(
            self, user: User, survey: Survey, files: Dict[str, UploadedFile]
    ):

        for field_name, uploaded_file in files.items():
            if not self._is_extension_supported(uploaded_file.name):
                raise UploadFileException(
                    "File extension not supported, must be one of "
                    + ",".join(settings.MEDIA_SUPPORTED_EXTENSIONS)
                )

        for field_name, uploaded_file in files.items():
            survey_file = SurveyFile.objects.create(survey=survey)
            survey_file.file = uploaded_file
            survey_file.save()

    @requires_permission("edit", obj_param="survey")
    def add_uploaded_files_to_evidence_section(
            self,
            user: User,
            survey: Survey,
            evidence_section: SurveyEvidenceSection,
            files: Dict[str, UploadedFile],
    ):

        for field_name, uploaded_file in files.items():
            if not self._is_extension_supported(uploaded_file.name):
                raise UploadFileException(
                    "File extension not supported, must be one of "
                    + " ,".join(settings.MEDIA_SUPPORTED_EXTENSIONS)
                )

        for field_name, uploaded_file in files.items():
            evidence_file = SurveyEvidenceFile.objects.create(
                evidence_section=evidence_section
            )
            evidence_file.file = uploaded_file
            evidence_file.save()

    @requires_permission("edit", obj_param="survey")
    def remove_file(self, user: User, survey: Survey, file: SurveyFile):
        file.delete()

    @requires_permission("edit", obj_param="survey")
    def remove_evidence_file(
            self, user: User, survey: Survey, file: SurveyEvidenceFile
    ):
        file.delete()

    @staticmethod
    def generate_mock_responses(user: User, survey: Survey, num_responses: int = 10):
        """
        Generate a number of mock responses
        """
        if not user.is_superuser:
            raise PermissionDenied("Must be superuser to use this feature")

        survey.generate_mock_responses(num_responses=num_responses)
