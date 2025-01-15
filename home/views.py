from lib2to3.fixes.fix_input import context

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView

from survey.models import Survey
from .mixins import OrganisationRequiredMixin
from .models import Organisation, Project, OrganisationMembership, ProjectOrganisation
from django.shortcuts import get_object_or_404, render
from django.views import View
from .forms import ManagerSignupForm, ManagerLoginForm, UserProfileForm
from django.contrib.auth import login
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from .permissions import can_view_project, can_edit_project
from .services import ProjectAccessService

from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.shortcuts import get_object_or_404

User = get_user_model()


class SignupView(CreateView):
    form_class = ManagerSignupForm
    template_name = "home/register.html"

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
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
    login_url = "login"

    def get(self, request):

        return render(request, self.template_name, {})


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = "home/profile.html"
    success_url = reverse_lazy("profile")

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Your profile has been successfully updated.")
        return super().form_valid(form)

    def form_invalid(self, form):
        print(form.errors)  # Output form errors to the console
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


# class PasswordResetExpiredView(TemplateView):  # leave for now
#     template_name = 'home/password_reset_expired.html'


class MyOrganisationView(LoginRequiredMixin, OrganisationRequiredMixin, ListView):
    template_name = "organisation/organisation.html"
    context_object_name = "projects"
    paginate_by = 10

    def get_queryset(self):
        organisation = self.request.user.organisation_set.first()
        projects = Project.objects.filter(
            projectorganisation__organisation=organisation
        ).annotate(survey_count=Count("survey"))
        return projects

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organisation = self.request.user.organisation_set.first()
        context["organisation"] = organisation

        context["can_edit"] = {
            project.id: can_edit_project(self.request.user, project)
            for project in context["projects"]
        }
        context["can_create"] = OrganisationMembership.objects.filter(
            user=self.request.user, role="ADMIN"
        ).exists()

        user_orgs = set(
            OrganisationMembership.objects.filter(user=self.request.user).values_list(
                "organisation_id", flat=True
            )
        )

        context["project_orgs"] = {
            project.id: [
                org for org in project.organisations.all() if org.id in user_orgs
            ]
            for project in context["projects"]
        }

        return context


class OrganisationCreateView(LoginRequiredMixin, CreateView):
    model = Organisation
    template_name = "organisation/create.html"
    fields = ["name", "description"]

    def get_success_url(self):
        return reverse_lazy("myorganisation")

    def form_valid(self, form):
        super().form_valid(form)
        # Add user that creates the org as admin
        OrganisationMembership.objects.create(
            organisation=self.object, user=self.request.user, role="ADMIN"
        )

        return redirect("myorganisation")


class ProjectView(LoginRequiredMixin, ListView):
    template_name = "projects/project.html"
    context_object_name = "surveys"
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        # Check if user is allowed to access the project
        try:
            self.project = Project.objects.get(id=self.kwargs["project_id"])
        except Project.DoesNotExist:
            messages.error(request, "Project not found.")
            return redirect("myorganisation")

        if not can_view_project(request.user, self.project):
            messages.error(
                request,
                f"You do not have permission to view the project {self.project.name}.",
            )
            return redirect("myorganisation")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Survey.objects.filter(project_id=self.kwargs["project_id"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = Project.objects.get(id=self.kwargs["project_id"])
        context["can_edit"] = can_edit_project(self.request.user, self.project)

        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    fields = ["name"]
    template_name = "projects/create.html"

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        # TODO: Check user allowed to create project in the org
        result = super().form_valid(form)
        organisation = Organisation.objects.get(id=self.kwargs["organisation_id"])
        # Link to the organisation
        ProjectOrganisation.objects.create(
            project=self.object, organisation=organisation, added_by=self.request.user
        )
        return result


class ProjectEditView(LoginRequiredMixin, UpdateView):
    model = Project
    template_name = "projects/edit.html"
    fields = ["name"]
    context_object_name = "project"

    def get_object(self, queryset=None):
        # Get the project with related organizations
        project = get_object_or_404(
            Project.objects.prefetch_related(
                "organisations",
                "organisations__organisationmembership_set"
            ),
            id=self.kwargs["project_id"]
        )

        # Check if user has edit permissions
        if not project.user_can_edit(self.request.user):
            raise PermissionDenied("You don't have permission to edit this project.")

        return project

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get user's org
        user_orgs = set(
            OrganisationMembership.objects.filter(
                user=self.request.user
            ).values_list("organisation_id", flat=True)
        )

        # Get the org that the user is a member of and are linked to the project
        context["project_orgs"] = [
            org for org in self.object.organisations.all()
            if org.id in user_orgs
        ]

        # Check if user can manage org for this project
        context["can_manage_orgs"] = any(
            membership.role == "ADMIN"
            for org in context["project_orgs"]
            for membership in org.organisationmembership_set.all()
            if membership.user == self.request.user
        )

        return context

    def get_success_url(self):
        return reverse("myorganisation")

    def form_valid(self, form):
        # Perform the update
        response = super().form_valid(form)
        return response
