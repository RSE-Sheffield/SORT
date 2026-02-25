from typing import Optional

import django.contrib.auth.views
import invitations.models
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from ..forms.manager_login import ManagerLoginForm
from ..forms.manager_signup import ManagerSignupForm
from ..forms.user_profile import UserProfileForm
from ..services import organisation_service

User = get_user_model()


class SignupView(CreateView):
    form_class = ManagerSignupForm
    template_name = "home/register.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._invitation: Optional[invitations.models.Invitation] = None

    @property
    def invitation(self) -> invitations.models.Invitation:
        """
        The user invite that was emailed to the new user. Each
        invitation is uniquely identified by its secret key and email address.
        """
        if self._invitation is None:
            try:
                self._invitation = invitations.models.Invitation.objects.get(
                    key=self.kwargs["key"]
                )
            # This signup must have an invitation
            except invitations.models.Invitation.DoesNotExist:
                raise PermissionDenied("You must be invited to sign up.")
        return self._invitation

    def get_context_data(self, **context):
        context = super().get_context_data(**context)

        # The invited user will be invited to the same organisation
        # as the manager who invited them.
        context["organisation"] = organisation_service.get_user_organisation(
            self.invitation.inviter
        )
        context["email"] = self.invitation.email

        return context

    def get_initial(self):
        initial = super().get_initial()
        initial["key"] = self.invitation.key
        return initial

    def form_valid(self, form):
        user = form.save()
        login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect(reverse_lazy("dashboard"))


class LogoutInterfaceView(LogoutView):
    success_url = reverse_lazy("landing")


class LoginInterfaceView(LoginView):
    template_name = "home/login.html"
    form_class = ManagerLoginForm
    success_url = reverse_lazy("dashboard")

    def form_invalid(self, form):
        messages.error(self.request, "Invalid email or password.")
        return super().form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = "home/profile.html"
    success_url = reverse_lazy("profile")

    def get_object(self, queryset=None) -> User:
        """
        Get the current user.
        """
        # We only ever want to be able to retrieve the authenticated user
        if queryset is not None:
            raise ValueError("queryset is not None")
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Your profile has been successfully updated.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, "There was an error updating your profile. Please try again."
        )
        return super().form_invalid(form)


class CustomPasswordResetView(PasswordResetView):
    template_name = "home/password_reset_form.html"
    email_template_name = "home/password_reset_email.html"
    success_url = reverse_lazy("password_reset_done")
    subject_template_name = "home/password_reset_subject.txt"


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "home/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "home/password_reset_done.html"


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "home/password_reset_complete.html"


class PasswordChangeView(django.contrib.auth.views.PasswordChangeView):
    def form_valid(self, form):
        messages.success(self.request, "Your password has been changed.")
        return super().form_valid(form=form)
