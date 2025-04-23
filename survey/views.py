import json
import logging
import mimetypes
import os.path

import django.core.mail
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.files.uploadhandler import UploadFileException
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.context_processors import csrf
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import DeleteView, FormView, UpdateView
from django.views.generic.edit import CreateView

from home.models import Project
from survey.services import survey_service

from .forms import InvitationForm
from .models import (
    Survey,
    SurveyEvidenceFile,
    SurveyEvidenceSection,
    SurveyImprovementPlanSection,
    SurveyResponse,
)
from .services.survey import InvalidInviteTokenException

logger = logging.getLogger(__name__)


class SurveyView(LoginRequiredMixin, View):
    """
    Manager's view of a survey to be sent out. The manager is able to
    configure what fields are included in the survey on this page.
    """

    def get(self, request: HttpRequest, pk: int):
        return self.render_survey_page(request, pk)

    def post(self, request: HttpRequest, pk: int):
        return self.render_survey_page(request, pk, is_post=True)

    def render_survey_page(self, request: HttpRequest, pk: int, is_post=False):
        context = {}
        survey = survey_service.get_survey(
            request.user, pk
        )  # Check that we're allowed to get the survey
        context["survey"] = survey
        context["first_evidence_section"] = (
            SurveyEvidenceSection.objects.filter(survey=survey)
            .order_by("section_id")
            .first()
        )
        context["first_improve_section"] = (
            SurveyImprovementPlanSection.objects.filter(survey=survey)
            .order_by("section_id")
            .first()
        )
        context["invite_link"] = survey.get_invite_link(request)
        context["responses_count"] = SurveyResponse.objects.filter(
            survey=survey
        ).count()
        context["can_edit"] = {survey.id: survey_service.can_edit(request.user, survey)}
        context["request"] = request
        return render(request, "survey/survey.html", context)


class SurveyCreateView(LoginRequiredMixin, CreateView):
    model = Survey
    template_name = "survey/create.html"
    fields = ["name", "description"]

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        result = super().form_valid(form)
        project = get_object_or_404(Project, pk=self.kwargs["project_id"])
        survey_service.initialise_survey(self.request.user, project, self.object)
        return result


class SurveyEditView(LoginRequiredMixin, UpdateView):
    model = Survey
    template_name = "survey/edit.html"
    fields = ["name", "description"]
    context_object_name = "survey"

    def form_valid(self, form):
        if survey_service.can_edit(self.request.user, self.object):
            messages.info(self.request, f"Survey {self.object.name} updated")
            return super().form_valid(form)
        else:
            messages.error(
                self.request, "You do not have permission to edit this survey."
            )
            return redirect("survey", pk=self.object.pk)

    def get_success_url(self):
        project_pk = self.object.project.pk
        return reverse_lazy("project", kwargs={"project_id": project_pk})


class SurveyDeleteView(LoginRequiredMixin, DeleteView):
    model = Survey
    template_name = "survey/delete.html"
    context_object_name = "survey"

    def form_valid(self, form):
        if survey_service.can_delete(self.request.user, self.object):
            messages.info(self.request, f"Survey {self.object.name} deleted")
            return super().form_valid(form)
        else:
            messages.error(
                self.request, "You do not have permission to delete this survey."
            )
            return redirect("survey", pk=self.object.pk)

    def get_success_url(self):
        project_pk = self.object.project.pk
        return reverse_lazy("project", kwargs={"project_id": project_pk})


class SurveyConfigureView(LoginRequiredMixin, View):

    def get(self, request: HttpRequest, pk: int):
        return self.render_survey_config_view(request, pk, is_post=False)

    def post(self, request: HttpRequest, pk: int):
        return self.render_survey_config_view(request, pk, is_post=True)

    def render_survey_config_view(self, request: HttpRequest, pk: int, is_post: bool):
        context = {}
        # TODO: Error handling when object not found
        survey = get_object_or_404(Survey, pk=pk)
        context["survey"] = survey
        context["csrf"] = str(csrf(self.request)["csrf_token"])
        context["can_edit"] = {survey.id: survey_service.can_edit(request.user, survey)}

        if is_post:
            if (
                "survey_body_path" in request.POST
                and "consent_config" in request.POST
                and "demography_config" in request.POST
            ):
                consent_config = json.loads(request.POST.get("consent_config", None))
                demography_config = json.loads(
                    request.POST.get("demography_config", None)
                )
                survey_body_path = request.POST.get("survey_body_path", None)
                survey_service.update_consent_demography_config(
                    request.user,
                    survey,
                    consent_config=consent_config,
                    demography_config=demography_config,
                    survey_body_path=survey_body_path,
                )
                messages.info(request, "Survey configuration saved")
                return redirect("survey", pk=survey.pk)

        return render(
            request=request,
            template_name="survey/survey_configure.html",
            context=context,
        )


class SurveyGenerateMockResponsesView(LoginRequiredMixin, View):

    def post(self, request: HttpRequest, pk: int):
        if "num_responses" in request.POST:
            num_responses = int(request.POST["num_responses"])
            survey = Survey.objects.get(pk=pk)
            survey_service.generate_mock_responses(request.user, survey, num_responses)
            messages.success(request, f"Generated {num_responses} mock responses")
        else:
            messages.error(request, "Could not generate mock responses")

        return redirect("survey", pk=pk)


class SurveyExportView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, pk: int):
        survey = survey_service.get_survey(request.user, pk)
        output_csv = survey_service.export_csv(self.request.user, survey)
        response = HttpResponse(output_csv, content_type="text/csv")
        file_name = f"survey_{survey.id}.csv"
        response["Content-Disposition"] = f"inline; filename={file_name}"
        return response


class SurveyResponseDataView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, pk: int):
        survey = survey_service.get_survey(request.user, pk)
        context = {
            "survey": survey,
            "responses": [
                response.answers
                for response in SurveyResponse.objects.filter(survey=survey)
            ],
        }

        return render(request, "survey/survey_response_data.html", context)


class SurveyEvidenceGatheringView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, pk: int, section_id: int):
        survey = survey_service.get_survey(request.user, pk)
        evidence_section = SurveyEvidenceSection.objects.get(
            survey=survey, section_id=section_id
        )
        sections = SurveyEvidenceSection.objects.filter(survey=survey).order_by(
            "section_id"
        )

        files_list = []
        for file in evidence_section.files.all():
            delete_url = reverse("survey_evidence_remove_file", kwargs={"pk": file.pk})
            file_url = reverse("survey_evidence_file", kwargs={"pk": file.pk})
            files_list.append(
                {
                    "name": os.path.basename(file.file.name),
                    "deleteUrl": delete_url,
                    "fileUrl": file_url,
                }
            )

        context = {
            "survey": survey,
            "responses": [
                response.answers
                for response in SurveyResponse.objects.filter(survey=survey)
            ],
            "evidence_section": evidence_section,
            "section_config": survey.survey_config["sections"][
                evidence_section.section_id
            ],
            "sections": sections,
            "files_list": files_list,
            "csrf": str(csrf(self.request)["csrf_token"]),
        }

        return render(
            request=request,
            template_name="survey/evidence_gathering.html",
            context=context,
        )


class SurveyEvidenceUpdateView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int, section_id: int):
        survey = survey_service.get_survey(request.user, pk)
        evidence_section = SurveyEvidenceSection.objects.get(
            survey=survey, section_id=section_id
        )
        if "text" in request.POST:
            survey_service.update_evidence_section(
                request.user, survey, evidence_section, text=request.POST["text"]
            )

        return redirect("survey_evidence_gathering", pk=pk, section_id=section_id)


class SurveyFileUploadView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int):
        try:
            survey = survey_service.get_survey(request.user, pk)
            survey_service.add_uploaded_files(request.user, survey, request.FILES)
        except UploadFileException as e:
            logger.error(e)
            messages.error(request, str(e))
        return redirect("survey", pk=pk)


class SurveyEvidenceFileUploadView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int, section_id: int):

        try:
            evidence_section = SurveyEvidenceSection.objects.get(
                survey_id=pk, section_id=section_id
            )
            survey_service.add_uploaded_files_to_evidence_section(
                request.user, evidence_section.survey, evidence_section, request.FILES
            )

        except UploadFileException as e:
            logger.error(e)
            messages.error(request, str(e))

        return redirect("survey_evidence_gathering", pk=pk, section_id=section_id)


class SurveyEvidenceFileDeleteView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int):
        evidence_file = SurveyEvidenceFile.objects.get(pk=pk)
        survey_service.remove_evidence_file(
            request.user, evidence_file.evidence_section.survey, evidence_file
        )
        return redirect(
            request.META.get(
                "HTTP_REFERER",
                reverse_lazy(
                    "survey_evidence_gathering", kwargs={"pk": pk, "section_id": 0}
                ),
            )
        )


class SurveyEvidenceFileView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, pk: int):
        evidence_file = SurveyEvidenceFile.objects.get(pk=pk)
        if not survey_service.can_view(
            request.user, evidence_file.evidence_section.survey
        ):
            raise PermissionDenied("You do not have permission to view this survey.")
        file_path = evidence_file.file.path
        file = open(file_path, "rb")

        content_type, encoding = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = "application/octet-stream"
        response = HttpResponse(content=file, content_type=content_type)
        response["Content-Disposition"] = f"filename={evidence_file.file.name}"
        return response


class SurveyImprovementPlanView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, pk: int, section_id: int):
        survey = survey_service.get_survey(request.user, pk)
        evidence_section = SurveyEvidenceSection.objects.get(
            survey=survey, section_id=section_id
        )
        improve_section = SurveyImprovementPlanSection.objects.get(
            survey=survey, section_id=section_id
        )
        improve_sections = SurveyImprovementPlanSection.objects.filter(
            survey=survey
        ).order_by("section_id")

        files_list = []
        for file in evidence_section.files.all():
            delete_url = reverse("survey_evidence_remove_file", kwargs={"pk": file.pk})
            file_url = reverse("survey_evidence_file", kwargs={"pk": file.pk})
            files_list.append(
                {
                    "name": os.path.basename(file.file.name),
                    "deleteUrl": delete_url,
                    "fileUrl": file_url,
                }
            )

        context = {
            "survey": survey,
            "responses": [
                response.answers
                for response in SurveyResponse.objects.filter(survey=survey)
            ],
            "evidence_section": evidence_section,
            "improve_section": improve_section,
            "sections": improve_sections,
            "files_list": files_list,
            "update_url": reverse_lazy(
                "survey_improvement_plan_update",
                kwargs={"pk": survey.pk, "section_id": improve_section.section_id},
            ),
            "plan": improve_section.plan,
            "csrf": str(csrf(self.request)["csrf_token"]),
        }
        return render(
            request=request,
            template_name="survey/improvement_plan.html",
            context=context,
        )


class SurveyImprovementPlanUpdateView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int, section_id: int):
        survey = survey_service.get_survey(request.user, pk)
        improve_section = SurveyImprovementPlanSection.objects.get(
            survey=survey, section_id=section_id
        )
        data = request.POST["data"]
        survey_service.update_improvement_section(
            request.user, survey, improve_section, data
        )

        return redirect(
            request.META.get(
                "HTTP_REFERER",
                reverse_lazy(
                    "survey_improvement_plan",
                    kwargs={"pk": survey.pk, "section_id": improve_section.section_id},
                ),
            )
        )


class SurveyReportView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, pk: int):
        survey = survey_service.get_survey(request.user, pk)

        evidence_sections = {
            e_section.section_id: e_section
            for e_section in SurveyEvidenceSection.objects.filter(
                survey=survey
            ).order_by("section_id")
        }
        improve_sections = {
            i_section.section_id: i_section
            for i_section in SurveyImprovementPlanSection.objects.filter(
                survey=survey
            ).order_by("section_id")
        }

        sections = []
        for index, section in enumerate(survey.survey_config["sections"]):
            sections.append(
                {
                    "section_config": section,
                    "evidence": evidence_sections.get(index, None),
                    "improvement": improve_sections.get(index, None),
                }
            )

        # files_list = []
        # for file in evidence_section.files.all():
        #     delete_url = reverse("survey_evidence_remove_file", kwargs={"pk": file.pk})
        #     file_url = reverse("survey_evidence_file", kwargs={"pk": file.pk})
        #     files_list.append({
        #         "name": os.path.basename(file.file.name),
        #         "deleteUrl": delete_url,
        #         "fileUrl": file_url
        #     })

        context = {
            "survey": survey,
            "responses": [
                response.answers
                for response in SurveyResponse.objects.filter(survey=survey)
            ],
            "sections": sections,
            "csrf": str(csrf(self.request)["csrf_token"]),
            # "files_list": files_list,
        }

        return render(request, "survey/report.html", context)


class SurveyResponseView(View):
    """
    Participant's view of the survey. This view renders the survey configuration
    allowing participant to fill in the survey form and send it for processing.
    """

    def get(self, request: HttpRequest, token: str):
        return self.render_survey_response_page(request, token, is_post=False)

    def post(self, request: HttpRequest, token: str):
        return self.render_survey_response_page(request, token, is_post=True)

    def render_survey_response_page(
        self, request: HttpRequest, token: str, is_post: bool
    ):

        try:

            survey = survey_service.get_survey_from_token(token)
            # Context for rendering
            context = {}

            if is_post:
                # Only process if it's a post request

                # TODO: Server side value validation to make sure
                if "value" in request.POST:
                    responseValues = json.loads(request.POST.get("value", None))
                    survey_service.accept_response(survey, responseValues)
                    context["value"] = responseValues
                    return redirect("completion_page")

            context["survey"] = survey
            context["csrf"] = str(csrf(self.request)["csrf_token"])

            return render(
                request=request,
                template_name="survey/survey_response.html",
                context=context,
            )

        except InvalidInviteTokenException:
            return redirect("survey_link_invalid")


class SurveyLinkInvalidView(View):
    """
    Shown when a participant is trying to access the SurveyResponseView using an
    invalid pk or token.
    """

    def get(self, request):
        return render(request, "survey/survey_link_invalid_view.html")


class CompletionView(View):
    """
    Shown when a survey is completed by a participant.
    """

    def get(self, request):
        return render(request, "survey/completion.html")


class SurveyCreateInviteView(LoginRequiredMixin, View):

    def post(self, request: HttpRequest, pk: int):
        survey = get_object_or_404(Survey, pk=pk)
        survey_service.create_invitation(request.user, survey)
        return redirect("survey", pk=pk)


class InvitationView(FormView):
    model = Survey
    template_name = "invitations/send_invitation.html"
    form_class = InvitationForm

    def form_valid(self, form):
        recipient_list = tuple(form.cleaned_data["email"].replace(",", " ").split())
        message = form.data["message"]
        survey = Survey.objects.get(pk=self.kwargs["pk"])
        # Generate the survey link with the token
        survey_link = survey.get_invite_link(request=self.request)

        # Send the email
        # https://docs.djangoproject.com/en/5.1/topics/email/
        django.core.mail.send_mail(
            subject="Your SORT Survey Invitation",
            message=f"Click here to start the SORT survey:\n{survey_link}\n\n{message}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )

        # Show success message
        messages.success(self.request, f"Invitation sent to {len(recipient_list)} recipients.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("invite", kwargs=dict(pk=self.kwargs["pk"]))
