import json
import logging
import os.path
import mimetypes

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.files.uploadhandler import UploadFileException
from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.context_processors import csrf
from django.urls import reverse_lazy, reverse
from django.utils.http import content_disposition_header
from django.views import View
from django.views.generic import DeleteView, FormView, TemplateView, UpdateView
from django.views.generic.edit import CreateView
from django.conf import settings

from home.models import Project
from survey.services import survey_service
from .forms import InvitationForm
from .models import Survey
import logging

from .forms import InvitationForm
from .models import Survey, SurveyEvidenceSection, SurveyEvidenceFile
from .services.survey import InvalidInviteTokenException
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from .services.survey import SurveyService
from survey.dashboards.dashboard import get_survey_dashboard

logger = logging.getLogger(__name__)


class SurveyView(LoginRequiredMixin, View):
    login_url = '/login/'
    """
    Manager's view of a survey to be sent out. The manager is able to
    configure what fields are included in the survey on this page.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.survey_service = SurveyService()

    def get(self, request: HttpRequest, pk: int):
        return self.render_survey_page(request, pk)

    def post(self, request, pk):
        print("POST method called")
        return self.render_survey_page(request, pk)

    def get_survey_metrics(self, responses):
        section_averages = {}
        response_list = []

        for response in responses:
            answers = response.answers
            response_data = {
                'model': 'survey.surveyresponse',
                'pk': response.pk,
                'fields': {
                    'survey': response.survey_id,
                    'answers': answers
                }
            }
            response_list.append(response_data)

            for section_idx, section_values in enumerate(answers):
                section_name = f'section_{section_idx + 1}'
                numeric_values = [
                    value for value in section_values
                    if isinstance(value, (int, float)) and not isinstance(value, bool)
                ]

                if numeric_values:
                    if section_name not in section_averages:
                        section_averages[section_name] = []
                    section_average = round(sum(numeric_values) / len(numeric_values), 1)
                    section_averages[section_name].append(section_average)

        final_averages = {
            section: round(sum(values) / len(values), 1)
            for section, values in section_averages.items()
            if values
        }

        return {
            'section_averages': final_averages,
            'survey_responses': response_list
        }

    def render_survey_page(self, request, pk):
    context = {}
    survey = survey_service.get_survey(request.user, pk)  # Check that we're allowed to get the survey
    responses = survey.survey_response.all()
    context["has_responses"] = responses.exists()
    if context["has_responses"]:
        get_survey_dashboard(survey.id)  # Only get the survey for a given id
        context["dashboard_name"] = f"SurveyDashboard_{survey.id}"
    context["survey"] = survey
    context["first_evidence_section"] = SurveyEvidenceSection.objects.filter(survey=survey).order_by(
        'section_id').first()
    context["invite_link"] = survey.get_invite_link(request)
    context["can_edit"] = {
        survey.id: survey_service.can_edit(request.user, survey)
    }
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
        context["can_edit"] = {
            survey.id: survey_service.can_edit(request.user, survey)
        }

        if is_post:
            if "consent_config" in request.POST and "demography_config" in request.POST:
                consent_config = json.loads(request.POST.get("consent_config", None))
                demography_config = json.loads(
                    request.POST.get("demography_config", None)
                )
                survey_service.update_consent_demography_config(request.user,
                                                                survey, consent_config, demography_config
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
        survey = Survey.objects.get(pk=pk)
        output_csv = survey_service.export_csv(self.request.user, survey)
        response = HttpResponse(output_csv, content_type="text/csv")
        file_name = f"survey_{survey.id}.csv"
        response["Content-Disposition"] = f"inline; filename={file_name}"
        return response


section_titles = [
    "A. Releasing Potential",
    "B. Embedding Research",
    "C. Linkages and Leadership",
    "D. Inclusive research delivery",
    "E. Digital enabled research",
]


class SurveyEvidenceGatheringView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, pk: int, section_id: int):
        survey = Survey.objects.get(pk=pk)
        evidence_section = SurveyEvidenceSection.objects.get(survey=survey, section_id=section_id)
        sections = SurveyEvidenceSection.objects.filter(survey=survey).order_by("section_id")

        files_list = []
        for file in evidence_section.files.all():
            delete_url = reverse("survey_evidence_remove_file", kwargs={"pk": file.pk})
            file_url = reverse("survey_evidence_file", kwargs={"pk": file.pk})
            files_list.append({
                "name": os.path.basename(file.file.name),
                "deleteUrl": delete_url,
                "fileUrl": file_url
            })

        context = {
            "survey": survey,
            "evidence_section": evidence_section,
            "section_config": survey.survey_config["sections"][evidence_section.section_id],
            "sections": sections,
            "files_list": files_list,
            "csrf": str(csrf(self.request)["csrf_token"])
        }

        return render(
            request=request,
            template_name="survey/evidence_gathering.html",
            context=context,
        )


class SurveyEvidenceUpdateView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int, section_id: int):
        survey = Survey.objects.get(pk=pk)
        evidence_section = SurveyEvidenceSection.objects.get(survey=survey, section_id=section_id)
        if "text" in request.POST:
            survey_service.update_evidence_section(request.user,
                                                   survey,
                                                   evidence_section,
                                                   text=request.POST["text"])

        return redirect(request.META["HTTP_REFERER"])


class SurveyFileUploadView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int):
        try:
            survey = Survey.objects.get(pk=pk)
            survey_service.add_uploaded_files(request.user, survey, request.FILES)
        except UploadFileException as e:
            logger.error(e)
            messages.error(request, str(e))
        return redirect(request.META["HTTP_REFERER"])


class SurveyEvidenceFileUploadView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int, section_id: int):

        try:
            evidence_section = SurveyEvidenceSection.objects.get(survey_id=pk, section_id=section_id)
            survey_service.add_uploaded_files_to_evidence_section(request.user,
                                                                  evidence_section.survey,
                                                                  evidence_section,
                                                                  request.FILES)

        except UploadFileException as e:
            logger.error(e)
            messages.error(request, str(e))

        return redirect(request.META["HTTP_REFERER"])


class SurveyEvidenceFileDeleteView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, pk: int):
        evidence_file = SurveyEvidenceFile.objects.get(pk=pk)
        survey_service.remove_evidence_file(request.user, evidence_file.evidence_section.survey, evidence_file)
        return redirect(request.META["HTTP_REFERER"])


class SurveyEvidenceFileView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, pk: int):
        evidence_file = SurveyEvidenceFile.objects.get(pk=pk)
        if not survey_service.can_view(request.user, evidence_file.evidence_section.survey):
            raise PermissionDenied("You do not have permission to view this survey.")
        file_path = evidence_file.file.path
        file = open(file_path, "rb")

        content_type, encoding = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = "application/octet-stream"
        response = HttpResponse(content=file, content_type=content_type)
        response['Content-Disposition'] = f"filename={evidence_file.file.name}"
        return response


class SurveyImprovementPlanView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, pk: int):
        survey = Survey.objects.get(pk=pk)
        context = {"survey": survey}
        context["section_titles"] = section_titles
        return render(
            request=request,
            template_name="survey/improvement_plan.html",
            context=context,
        )


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
    success_url = reverse_lazy("success_invitation")

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        survey = Survey.objects.get(pk=self.kwargs["pk"])
        # Generate the survey link with the token
        survey_link = survey.get_invite_link()

        # Send the email
        send_mail(
            "Your Survey Invitation",
            f"Click here to start the survey: {survey_link}",
            "from@example.com",
            [email],
            fail_silently=False,
        )

        # Show success message
        messages.success(self.request, f"Invitation sent to {email}.")
        return super().form_valid(form)


class SuccessInvitationView(LoginRequiredMixin, TemplateView):
    template_name = "invitations/complete_invitation.html"
