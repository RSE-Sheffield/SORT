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
from .permissions import (
    can_create_projects,
    can_view_project,
    can_edit_project,
    get_project_permissions,
)
from .services import (
    OrganisationService,
    ProjectService
)

from .constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER

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

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.organisation = OrganisationService.get_user_organisation(request.user)

    def get_queryset(self):
        return OrganisationService.get_organisation_projects(self.organisation)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        projects = context["projects"]

        user_role = self.organisation.get_user_role(user)

        context.update(
            {
                "organisation": self.organisation,
                "can_edit": get_project_permissions(user, projects),
                "can_create": can_create_projects(user),
                "is_admin": user_role == ROLE_ADMIN,
                "is_project_manager": user_role == ROLE_PROJECT_MANAGER,
                "project_orgs": OrganisationService.get_user_accessible_organisations(
                    projects, user
                ),
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
        super().form_valid(form)
        OrganisationService.add_user_to_organisation(
            user=self.request.user,
            organisation=self.object,
            role=ROLE_ADMIN,
            added_by=self.request.user,
        )
        return redirect("myorganisation")


class ProjectView(LoginRequiredMixin, ListView):
    template_name = "projects/project.html"
    context_object_name = "surveys"
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
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
        user = self.request.user
        project = self.project

        context.update(
            {
                "project": project,
                "can_create": can_edit_project(user, project),
            }
        )

        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    fields = ["name"]
    template_name = "projects/create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organisation = Organisation.objects.get(id=self.kwargs["organisation_id"])
        context["organisation"] = organisation

        if not can_create_projects(self.request.user):
            messages.error(
                self.request,
                "You don't have permissions to create projects in this organisation.",
            )
            return redirect("myorganisation")

        return context

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        result = super().form_valid(form)

        organisation = Organisation.objects.get(id=self.kwargs["organisation_id"])
        ProjectService.link_project_to_organisation(
            project=self.object,
            organisation=organisation,
            user=self.request.user,
            permission="EDIT",  # Project creators get edit permission by default
        )

        return result


class ProjectEditView(LoginRequiredMixin, UpdateView):
    model = Project
    template_name = "projects/edit.html"
    fields = ["name"]
    context_object_name = "project"

    def get_object(self, queryset=None):
        project = get_object_or_404(
            Project.objects.prefetch_related(
                "organisations", "organisations__organisationmembership_set"
            ),
            id=self.kwargs["project_id"],
        )

        if not can_edit_project(self.request.user, project):
            messages.error(
                self.request, "You don't have permission to edit this project."
            )
            return redirect("myorganisation")

        return project

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get all organisations user has access to
        project_orgs = OrganisationService.get_user_accessible_organisations(
            [self.object], user
        ).get(self.object.id, [])

        # Get user's roles across organisations
        user_roles = {org.id: org.get_user_role(user) for org in project_orgs}

        context.update(
            {
                "project_orgs": project_orgs,
                "can_manage_orgs": any(
                    role == ROLE_ADMIN for role in user_roles.values()
                ),
                "is_project_manager": any(
                    role == ROLE_PROJECT_MANAGER for role in user_roles.values()
                ),
            }
        )

        return context

    def get_success_url(self):
        return reverse("myorganisation")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, f"Project {self.object.name} has been updated successfully."
        )
        return response
