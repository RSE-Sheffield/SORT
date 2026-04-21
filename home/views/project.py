from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from survey.models import Survey
from survey.services import survey_service

from ..constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER
from ..models import Organisation, Project
from ..services import project_service


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
