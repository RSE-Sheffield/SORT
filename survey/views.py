import json

from IPython.utils.coloransi import value
from django.core.mail import send_mail
from django.http import HttpRequest
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
from .mixins import TokenAuthenticationMixin

from .forms import create_dynamic_formset, InvitationForm
from .models import Survey, SurveyResponse
from .models import Invitation
from .misc import test_survey_config

import logging

logger = logging.getLogger(__name__)


class SurveyView(LoginRequiredMixin, View):
    """
    Manager's view of a survey to be sent out. The manager is able to
    configure what fields are included in the survey on this page.
    """
    login_url = '/login/'  # redirect to login if not authenticated

    def get(self, request, pk):
        return self.render_survey_page(request, pk)

    def post(self, request, pk):
        return self.render_survey_page(request, pk)

    def render_survey_page(self, request, pk):
        context = {}
        survey = get_object_or_404(Survey, pk=pk)

        context["survey"] = survey

        return render(request, 'survey/survey.html', context)


class SurveyCreateView(LoginRequiredMixin, CreateView):
    model = Survey
    template_name = "survey/create.html"
    fields = ["name", "description"]

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        result = super().form_valid(form)
        project = Project.objects.get(id=self.kwargs["project_id"])
        self.object.project = project

        # TODO: Make a proper loader function
        with open("data/survey_config/consent_only_config.json") as f:
            consent_config = json.load(f)
            self.object.consent_config = consent_config

        with open("data/survey_config/demography_only_config.json") as f:
            demo_config = json.load(f)
            self.object.demography_config = demo_config

        self.object.survey_config = test_survey_config  # TODO: Using a test config for now, to be replaced
        self.object.save()
        return result


class SurveyConfigureView(LoginRequiredMixin, View):

    def get(self, request: HttpRequest, pk: int):
        return self.render_survey_config_view(request, pk, is_post=False)

    def post(self, request: HttpRequest, pk: int):
        return self.render_survey_config_view(request, pk,  is_post=True)

    def render_survey_config_view(self, request: HttpRequest, pk: int, is_post: bool):
        context = {}
        # TODO: Error handling when object not found
        survey = get_object_or_404(Survey, pk=pk)
        context["survey"] = survey
        context["csrf"] = str(csrf(self.request)["csrf_token"])


        if is_post:
            if "consent_config" in request.POST and "demography_config" in request.POST:
                survey.consent_config = json.loads(request.POST["consent_config"])
                survey.demography_config = json.loads(request.POST["demography_config"])
                with open("data/survey_config/sort_only_config.json") as f:
                    sort_config = json.load(f)
                    merged_sections = survey.consent_config["sections"] + sort_config["sections"] + survey.demography_config["sections"]
                    survey.survey_config = {
                        "sections": merged_sections
                    }
                survey.save()

        return render(request=request,
                      template_name="survey/survey_configure.html",
                      context=context)


# TODO: Add TokenAuthenticationMixin after re-enabling the token
class SurveyResponseView(View):
    """
    Participant's view of the survey. This view renders the survey configuration
    allowing participant to fill in the survey form and send it for processing.
    """

    def get(self, request: HttpRequest, pk: int, token: str):
        return self.render_survey_response_page(request, pk, token, is_post=False)

    def post(self, request: HttpRequest, pk: int, token: str):
        return self.render_survey_response_page(request, pk, token, is_post=True)

    def render_survey_response_page(self,
                                    request: HttpRequest,
                                    pk: int,
                                    token: str,
                                    is_post: bool):



        # Check token

        # TODO: Re-enable token once the invitation UI is in place
        # if not self.validate_token(token):
        #     messages.error(request, "Invalid or expired invitation token.")
        #     logger.error(f"Token validation failed.")
        #     return redirect('survey_link_invalid')

        # Get the survey object and config
        survey = get_object_or_404(Survey, pk=pk)
        survey_config = survey.survey_config

        # TODO: Check that config is valid

        # Context for rendering
        context = {}

        context["pk"] = pk
        context["token"] = token

        if is_post:
            # TODO: Server side value validation to make sure
            # Only process if it's a post request
            if "value" in request.POST:
                responseValues = json.loads(request.POST.get("value",None))
                context["value"] = responseValues
                SurveyResponse.objects.create(survey=survey, answers=responseValues)



        context["survey"] = survey
        context["csrf"] = str(csrf(self.request)["csrf_token"])

        return render(request=request,
                      template_name='survey/survey_response.html',
                      context=context)

    def validate_token(self, token):

        is_valid = Invitation.objects.filter(token=token).exists()

        if is_valid:
            logger.info("Token is valid.")
        else:
            logger.warning("Token is invalid or expired.")
        return is_valid


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


class InvitationView(FormView):
    template_name = 'invitations/send_invitation.html'
    form_class = InvitationForm
    success_url = reverse_lazy('success_invitation')

    def form_valid(self, form):
        email = form.cleaned_data['email']

        survey = Survey.objects.first()

        invitation = Invitation.objects.create(survey=survey)

        token = invitation.token

        # Generate the survey link with the token
        survey_link = f"http://localhost:8000/survey/{survey.pk}/{token}/"

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
