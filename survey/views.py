from django.core.mail import send_mail
from django.http import HttpRequest
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView, TemplateView, DetailView
from django.views.generic.edit import CreateView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

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

        self.object.survey_config = test_survey_config # TODO: Using a test config for now, to be replaced
        self.object.save()
        return result

class SurveyConfigureView(LoginRequiredMixin, DetailView):
    model = Survey
    template_name = "survey/survey_configure.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["testdata"] = ["one", "two", "three"]
        return context

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

        survey_form_session_key = "survey_form_session"

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

        # Gets the session data or sets it anew with section starting from 0
        session_data = {"section": 0}
        if is_post:
            if survey_form_session_key in request.session:
                session_data = request.session[survey_form_session_key]

        current_section = session_data["section"]
        survey_form_set = create_dynamic_formset(survey_config["sections"][current_section]["fields"])

        if is_post:
            # Only process if it's a post request

            # Validate current form
            survey_form = survey_form_set(request.POST)
            if survey_form.is_valid():
                logger.info("Form validated")
                # Store form data
                if "data" not in session_data:
                    session_data["data"] = []
                session_data["data"].append(survey_form.cleaned_data)

                current_section += 1
                if current_section < len(survey_config["sections"]):
                    # Go to next section
                    logger.info(f"Redirecting to next section")
                    # Store section's data
                    session_data["section"] = current_section
                    # Display the next section
                    survey_form = create_dynamic_formset(survey_config["sections"][current_section]["fields"])
                else:
                    # No more sections so it's finished
                    logger.info("No more questions. Redirecting to completion page.")

                    # Save data
                    SurveyResponse.objects.create(survey=survey, answers=session_data["data"])

                    # Delete session key
                    del request.session[survey_form_session_key]
                    request.session.modified = True

                    # TODO: Re-enable this once token has been enabled
                    # Invalidate token
                    # token = Invitation.objects.get(token=token)
                    # token.used = True
                    # token.save()

                    # Go to the completion page
                    return redirect('completion_page')
            else:
                logger.info("Form invalid")
        else:
            # Return empty form if it's a get request
            survey_form = survey_form_set()

        request.session[survey_form_session_key] = session_data
        context["title"] = survey_config["sections"][session_data["section"]]["title"]
        context["form"] = survey_form

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
        return render(request, "survey/survey_link_invalid_view.html" )

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
