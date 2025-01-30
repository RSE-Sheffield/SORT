import json
from typing import Any

from django.shortcuts import get_object_or_404

from home.services import BasePermissionService
from home.models import User, Project
from home.services.base import requires_permission
from survey.models import Invitation, Survey, SurveyResponse

import logging
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

        survey.survey_config = {}
        survey.save()

        return survey

    def update_consent_demography_config(self,
                                         survey: Survey,
                                         consent_config,
                                         demography_config) -> Survey:
        survey.consent_config = consent_config
        survey.demography_config = demography_config

        with open("data/survey_config/sort_only_config.json") as f:
            sort_config = json.load(f)
            merged_sections = survey.consent_config["sections"] + sort_config["sections"] + survey.demography_config[
                "sections"]
            survey.survey_config = {
                "sections": merged_sections
            }
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




