from django.views.generic.edit import FormView
from django.core.mail import send_mail
from django.contrib import messages
from .forms import InvitationForm
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from survey.models import Questionnaire
from invites.models import Invitation
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseForbidden


class InvitationView(FormView):

    template_name = 'invitations/send_invitation.html'
    form_class = InvitationForm
    success_url = reverse_lazy('success_invitation')

    def form_valid(self, form):
        email = form.cleaned_data['email']

        questionnaire = Questionnaire.objects.first()

        invitation = Invitation.objects.create(questionnaire=questionnaire)

        token = invitation.token

        # Generate the survey link with the token
        survey_link = f"http://localhost:8000/survey/{questionnaire.pk}/{token}/"

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
