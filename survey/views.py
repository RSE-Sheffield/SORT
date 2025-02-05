import json
from multiprocessing.managers import Token

from IPython.utils.coloransi import value
from django.core.mail import send_mail
from django.http import HttpRequest, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.functional import unpickle_lazyobject
from django.views import View
from django.views.generic import FormView, TemplateView, DetailView, UpdateView
from django.views.generic.edit import CreateView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.context_processors import csrf
from home.models import Project
from survey.services import survey_service
from .mixins import TokenAuthenticationMixin

from .forms import create_dynamic_formset, InvitationForm
from .models import Survey, SurveyResponse
from .models import Invitation
from .misc import test_survey_config

import logging

from .services.survey import InvalidInviteTokenException

logger = logging.getLogger(__name__)


class SurveyView(LoginRequiredMixin, View):
    """
    Manager's view of a survey to be sent out. The manager is able to
    configure what fields are included in the survey on this page.
    """
    login_url = '/login/'  # redirect to login if not authenticated

    def get(self, request: HttpRequest, pk: int):
        return self.render_survey_page(request, pk)

    def post(self, request: HttpRequest, pk: int):
        return self.render_survey_page(request, pk, is_post=True)

    def render_survey_page(self, request: HttpRequest, pk: int, is_post=False):
        context = {}
        survey = survey_service.get_survey(survey_id=pk)
        context["survey"] = survey
        context["invite_link"] = survey.get_invite_link(request)

        return render(request, 'survey/survey.html', context)


class SurveyCreateView(LoginRequiredMixin, CreateView):
    model = Survey
    template_name = "survey/create.html"
    fields = ["name", "description"]
    login_url = '/login/'

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        result = super().form_valid(form)
        project = Project.objects.get(pk=self.kwargs["project_id"])
        survey_service.create_survey(self.object, project)
        return result


class SurveyConfigureView(LoginRequiredMixin, View):
    login_url = '/login/'

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

        if is_post:
            if "consent_config" in request.POST and "demography_config" in request.POST:
                consent_config = json.loads(request.POST.get("consent_config", None))
                demography_config = json.loads(request.POST.get("demography_config", None))
                survey_service.update_consent_demography_config(survey, consent_config, demography_config)
                # TODO: Return success message

        return render(request=request,
                      template_name="survey/survey_configure.html",
                      context=context)


# TODO: Add TokenAuthenticationMixin after re-enabling the token
class SurveyResponseView(View):
    """
    Participant's view of the survey. This view renders the survey configuration
    allowing participant to fill in the survey form and send it for processing.
    """

    def get(self, request: HttpRequest, token: str):
        return self.render_survey_response_page(request, token, is_post=False)

    def post(self, request: HttpRequest, token: str):
        return self.render_survey_response_page(request, token, is_post=True)

    def render_survey_response_page(self,
                                    request: HttpRequest,
                                    token: str,
                                    is_post: bool):

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

            return render(request=request,
                          template_name='survey/survey_response.html',
                          context=context)

        except InvalidInviteTokenException as e:
            return redirect('survey_link_invalid')


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
        messages.info(request, "You have completed the survey.")
        return render(request, "survey/completion.html")


class SurveyCreateInviteView(LoginRequiredMixin, View):
    login_url = '/login/'

    def post(self, request: HttpRequest, pk: int):
        survey = get_object_or_404(Survey, pk=pk)
        survey_service.create_invitation(survey)
        return redirect("survey", pk=pk)


class InvitationView(FormView):
    model = Survey
    template_name = 'invitations/send_invitation.html'
    form_class = InvitationForm
    success_url = reverse_lazy('success_invitation')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        survey = Survey.objects.get(pk=self.kwargs["pk"])
        # Generate the survey link with the token
        survey_link = survey.get_invite_link()

        # Send the email
        send_mail(
            'Your Survey Invitation',
            f'Click here to start the survey: {survey_link}',
            'from@example.com',
            [email],
            fail_silently=False,
        )

        # Show success message
        messages.success(self.request, f'Invitation sent to {email}.')
        return super().form_valid(form)


class SuccessInvitationView(LoginRequiredMixin, TemplateView):
    template_name = 'invitations/complete_invitation.html'
