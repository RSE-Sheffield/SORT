from typing import Optional

import django.contrib.auth.views
import django.http
import invitations.models
import invitations.views
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
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

from survey.models import Survey
from survey.services import survey_service

from .constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER
from .forms.manager_login import ManagerLoginForm
from .forms.manager_signup import ManagerSignupForm
from .forms.user_profile import UserProfileForm
from .mixins import OrganisationRequiredMixin
from .models import Organisation, OrganisationMembership, Project
from .services import organisation_service, project_service

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
        return redirect(reverse_lazy("home"))


class LogoutInterfaceView(LogoutView):
    success_url = reverse_lazy("login")


class LoginInterfaceView(LoginView):
    template_name = "home/login.html"
    form_class = ManagerLoginForm
    success_url = reverse_lazy("home")

    def form_invalid(self, form):
        messages.error(self.request, "Invalid email or password.")
        return super().form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)


class HomeView(LoginRequiredMixin, View):
    template_name = "home/welcome.html"
    context_object_name = "projects"

    def get(self, request):
        user = self.request.user
        # all projects for current user
        projects = project_service.get_user_projects(user)
        return render(request, self.template_name, context=dict(projects=projects))


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


class MyOrganisationView(LoginRequiredMixin, OrganisationRequiredMixin, ListView):
    template_name = "organisation/organisation.html"
    context_object_name = "projects"
    paginate_by = 10

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.organisation = organisation_service.get_user_organisation(request.user)

        if not self.organisation:
            messages.error(request, "You are not a member of any organisation.")
            return redirect("organisation_create")

    def get_queryset(self):
        queryset = organisation_service.get_organisation_projects(
            organisation=self.organisation,
            user=self.request.user,
        )

        search_query = self.request.GET.get("q")
        if search_query:
            queryset = queryset.filter(Q(name__icontains=search_query))

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        projects = context["projects"]
        user_role = self.organisation.get_user_role(user)

        context.update(
            {
                "organisation": self.organisation,
                "can_edit": {
                    project.id: project_service.can_edit(user, project)
                    for project in projects
                },
                "can_create": project_service.can_create(user, self.organisation),
                "is_admin": user_role == ROLE_ADMIN,
                "is_project_manager": user_role == ROLE_PROJECT_MANAGER,
                "current_search": self.request.GET.get("q", ""),
            }
        )
        return context


class OrganisationCreateView(LoginRequiredMixin, CreateView):
    model = Organisation
    template_name = "organisation/create.html"
    fields = ["name", "description"]

    def get_success_url(self):
        return reverse_lazy("myorganisation")

    def form_valid(self, form):
        try:
            organisation = organisation_service.create_organisation(
                user=self.request.user,
                name=form.cleaned_data["name"],
                description=form.cleaned_data["description"],
            )
            self.object = organisation
            return redirect(self.get_success_url())
        except PermissionDenied:
            messages.error(
                self.request, "You don't have permission to create organisations."
            )
            return redirect("home")


class ProjectView(LoginRequiredMixin, ListView):
    template_name = "projects/project.html"
    context_object_name = "surveys"
    paginate_by = 10

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        try:
            self.project = Project.objects.get(id=kwargs.get("project_id"))
        except Project.DoesNotExist:
            self.project = None

    def get(self, request, *args, **kwargs):
        if not hasattr(self, "project") or not self.project:
            messages.error(request, "Project not found.")
            return redirect("myorganisation")

        if not project_service.can_view(request.user, self.project):
            messages.error(
                request,
                f"You do not have permission to view the project {self.project.name}.",
            )
            return redirect("myorganisation")

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Survey.objects.filter(project_id=self.kwargs["project_id"])

        # Add search if query exists
        search_query = self.request.GET.get("q")
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query)  # Only search by survey name
            )

        # Django requires consistent ordering for pagination
        return queryset.order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        project = self.project
        surveys = context["surveys"]

        can_edit = {}
        for survey in surveys:
            can_edit[survey.id] = survey_service.can_edit(user, survey)

        context.update(
            {
                "project": project,
                "can_create": project_service.can_edit(user, project),
                "current_search": self.request.GET.get("q", ""),
                "can_edit": can_edit,
            }
        )

        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    fields = ["name", "description"]
    template_name = "projects/create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organisation = Organisation.objects.get(id=self.kwargs["organisation_id"])
        context["organisation"] = organisation

        if not project_service.can_create(self.request.user, organisation):
            messages.error(
                self.request,
                "You don't have permission to create projects in this organisation.",
            )
            return redirect("myorganisation")

        return context

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        try:
            organisation = Organisation.objects.get(id=self.kwargs["organisation_id"])
            project = project_service.create_project(
                user=self.request.user,
                name=form.cleaned_data["name"],
                description=form.cleaned_data["description"],
                organisation=organisation,
            )
            self.object = project
            return redirect(self.get_success_url())
        except PermissionDenied:
            messages.error(self.request, "Permission denied")
            return redirect("myorganisation")


class ProjectEditView(LoginRequiredMixin, UpdateView):
    model = Project
    template_name = "projects/edit.html"
    fields = ["name", "description"]
    context_object_name = "project"

    def get_object(self, queryset=None):
        project = get_object_or_404(
            Project.objects.select_related("organisation"),
            id=self.kwargs["project_id"],
        )

        if not project_service.can_edit(self.request.user, project):
            messages.error(
                self.request, "You don't have permission to edit this project."
            )
            return redirect("myorganisation")

        return project

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        user_role = self.object.organisation.get_user_role(user)

        context.update(
            {
                "organisation": self.object.organisation,
                "is_admin": user_role == ROLE_ADMIN,
                "is_project_manager": user_role == ROLE_PROJECT_MANAGER,
            }
        )

        return context

    def get_success_url(self):
        return reverse("project", kwargs=dict(project_id=self.object.pk))

    def form_valid(self, form):
        try:
            project_service.update_project(
                user=self.request.user, project=self.object, data=form.cleaned_data
            )
            messages.success(
                self.request,
                f"Saved changes to {self.object}.",
            )
            return redirect(self.get_success_url())
        except PermissionDenied:
            messages.error(self.request, "Permission denied")
            return redirect("myorganisation")


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = "projects/delete.html"
    context_object_name = "project"

    def form_valid(self, form):
        if project_service.can_delete(self.request.user, self.object):
            messages.info(self.request, f"Project {self.object.name} has been deleted.")
            return super().form_valid(form)
        else:
            messages.error(
                self.request, "You don't have permission to delete this project."
            )
            return redirect("project", project_id=self.object.id)

    def get_success_url(self):
        return reverse_lazy("myorganisation")


class PasswordChangeView(django.contrib.auth.views.PasswordChangeView):
    def form_valid(self, form):
        messages.success(self.request, "Your password has been changed.")
        return super().form_valid(form=form)


class OrganisationMembershipListView(
    LoginRequiredMixin, OrganisationRequiredMixin, ListView
):
    model = OrganisationMembership
    context_object_name = "memberships"
    template_name = "organisation/members/list.html"

    @property
    def organisation(self) -> Organisation:
        return organisation_service.get_user_organisation(self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(organisation=self.organisation)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organisation"] = self.organisation
        return context


class MyOrganisationInviteView(
    LoginRequiredMixin, OrganisationRequiredMixin, invitations.views.SendInvite
):
    """
    Invite a new member to join an organisation via email.

    https://django-invitations.readthedocs.io/en/latest/usage.html
    """

    # Based on the template in the django-invitations plugin
    # https://github.com/jazzband/django-invitations/blob/master/invitations/templates/invitations/forms/_invite.html
    template_name = "organisation/members/create.html"


class MyOrganisationAcceptInviteView(invitations.views.AcceptInvite):
    """
    Accept an invitation to join an organisation as a manager.

    This inherits from the view in the django-invitations app, but
    also passes the key to the form to improve security.
    """

    def post(self, *args, **kwargs):
        import django.urls

        try:
            super().post(*args, **kwargs)
        # There is no public signup URL
        except django.urls.NoReverseMatch:
            pass

        # Signup requires a key from an invitation
        return redirect("signup", key=self.object.key)


class OrganisationMembershipDeleteView(
    LoginRequiredMixin, OrganisationRequiredMixin, SuccessMessageMixin, DeleteView
):
    """
    Remove a user from an organisation.
    """

    model = OrganisationMembership
    template_name = "organisation/members/delete.html"
    context_object_name = "organisation_membership"
    success_url = reverse_lazy("members")
    success_message = "The user was removed from the organisation."

    def form_valid(self, form):
        """
        After the confirmation form has been submitted successfully, remove the user from the organisation.
        """
        # Override this function so we can use the appropriate service
        organisation_service.remove_user_from_organisation(
            user=self.request.user,
            organisation=self.object.organisation,
            removed_user=self.object.user,
        )
        messages.success(
            self.request,
            message=f"The user {self.object.user} was removed from {self.object.organisation}.",
        )
        return django.http.HttpResponseRedirect(self.get_success_url())


class HelpView(LoginRequiredMixin, TemplateView):
    template_name = "about/help.html"


class TroubleshootingView(LoginRequiredMixin, TemplateView):
    template_name = "about/troubleshooting.html"


class LicenseAgreementView(LoginRequiredMixin, TemplateView):
    """
    End user license agreement
    """

    template_name = "about/end_user_license_agreement.html"


class PrivacyPolicyView(TemplateView):
    """
    Privacy policy and data protection notice
    """

    template_name = "about/privacy.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_date"] = timezone.now().strftime("%d %B %Y")
        return context


class ParticipantInformationView(TemplateView):
    """
    Participant information sheet for research study
    """

    template_name = "about/participant_information.html"
