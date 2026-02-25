"""
Staff management console.

This interface provides a dashboard overview of the app status. It's different from the /admin/ dashboard.
"""

from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import TemplateView, View

from home.mixins import StaffRequiredMixin
from home.models import Organisation, OrganisationMembership, Project, User
from survey.models import Survey, SurveyResponse


class ConsoleView(StaffRequiredMixin, TemplateView):
    template_name = "console/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["stats"] = {
            "organisations": Organisation.objects.count(),
            "users": User.objects.filter(is_active=True).count(),
            "projects": Project.objects.count(),
            "surveys": Survey.objects.count(),
            "responses": SurveyResponse.objects.count(),
        }

        # Recent activity feed
        context["recent_organisations"] = Organisation.objects.order_by("-created_at")[:5]
        context["recent_users"] = User.objects.filter(is_active=True).order_by("-date_joined")[:5]
        context["recent_surveys"] = Survey.objects.order_by("-created_at")[:5]

        return context


class ConsoleOrganisationListView(StaffRequiredMixin, TemplateView):
    template_name = "console/organisations.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organisations"] = Organisation.objects.annotate(
            members_count=Count("organisationmembership", distinct=True),
            project_count=Count("projects", distinct=True),
            survey_count=Count("projects__survey", distinct=True),
            response_count=Count("projects__survey__survey_response", distinct=True),
        ).order_by("name")
        return context


class ConsoleOrganisationDetailView(StaffRequiredMixin, TemplateView):
    template_name = "console/organisation_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = get_object_or_404(Organisation, pk=self.kwargs["pk"])
        context["organisation"] = org
        context["memberships"] = (
            OrganisationMembership.objects.filter(organisation=org)
            .select_related("user", "added_by")
            .order_by("role", "user__last_name", "user__first_name")
        )
        context["projects"] = org.projects.order_by("name")
        context["survey_count"] = Survey.objects.filter(project__organisation=org).count()
        return context


class ConsoleUserListView(StaffRequiredMixin, TemplateView):
    template_name = "console/users.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["users"] = User.objects.filter(is_active=True).order_by("last_name", "first_name")
        return context


class ConsoleUserDetailView(StaffRequiredMixin, TemplateView):
    template_name = "console/user_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(User, pk=self.kwargs["pk"])
        context["viewed_user"] = user
        context["memberships"] = (
            OrganisationMembership.objects.filter(user=user)
            .select_related("organisation", "added_by")
            .order_by("organisation__name")
        )
        context["projects_created"] = (
            Project.objects.filter(created_by=user)
            .select_related("organisation")
            .order_by("organisation__name", "name")
        )
        return context


class ConsoleProjectListView(StaffRequiredMixin, TemplateView):
    template_name = "console/projects.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org_id = self.request.GET.get("organisation")
        projects = Project.objects.select_related("organisation").order_by("organisation__name", "name")
        if org_id:
            projects = projects.filter(organisation_id=org_id)
            try:
                context["selected_organisation"] = Organisation.objects.get(pk=org_id)
                context["memberships"] = (
                    OrganisationMembership.objects.filter(organisation_id=org_id)
                    .select_related("user")
                    .order_by("role", "user__last_name", "user__first_name")
                )
            except Organisation.DoesNotExist:
                pass
        context["projects"] = projects
        context["organisations"] = Organisation.objects.order_by("name")
        return context


class ConsoleProjectDetailView(StaffRequiredMixin, TemplateView):
    template_name = "console/project_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_object_or_404(Project.objects.select_related("organisation", "created_by"), pk=self.kwargs["pk"])
        context["project"] = project
        context["surveys"] = Survey.objects.filter(project=project).order_by("-created_at")
        return context


class ConsoleSurveyDetailView(StaffRequiredMixin, TemplateView):
    template_name = "console/survey_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        survey = get_object_or_404(
            Survey.objects.select_related("project__organisation"), pk=self.kwargs["pk"]
        )
        context["survey"] = survey
        context["responses"] = survey.survey_response.order_by("-created_at")
        return context


class ConsoleSurveyListView(StaffRequiredMixin, TemplateView):
    template_name = "console/surveys.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org_id = self.request.GET.get("organisation")
        project_id = self.request.GET.get("project")

        surveys = Survey.objects.select_related("project__organisation").order_by("-created_at")

        if org_id:
            surveys = surveys.filter(project__organisation_id=org_id)
            try:
                context["selected_organisation"] = Organisation.objects.get(pk=org_id)
            except Organisation.DoesNotExist:
                pass

        if project_id:
            surveys = surveys.filter(project_id=project_id)
            try:
                context["selected_project"] = Project.objects.select_related("organisation").get(pk=project_id)
            except Project.DoesNotExist:
                pass

        context["surveys"] = surveys
        context["organisations"] = Organisation.objects.order_by("name")
        # Projects dropdown: scoped to selected org if present, otherwise all
        projects = Project.objects.select_related("organisation").order_by("organisation__name", "name")
        if org_id:
            projects = projects.filter(organisation_id=org_id)
        context["projects"] = projects
        return context


class ConsoleRemoveMemberView(StaffRequiredMixin, View):
    template_name = "console/remove_member_confirm.html"

    def _get_objects(self, org_pk, membership_pk):
        org = get_object_or_404(Organisation, pk=org_pk)
        membership = get_object_or_404(OrganisationMembership, pk=membership_pk, organisation=org)
        return org, membership

    def get(self, request, org_pk, membership_pk):
        org, membership = self._get_objects(org_pk, membership_pk)
        return self.render_to_response({"organisation": org, "membership": membership})

    def post(self, request, org_pk, membership_pk):
        org, membership = self._get_objects(org_pk, membership_pk)
        membership.delete()
        messages.success(request, f"{membership.user} removed from {org.name}.")
        return redirect("admin_organisation_detail", pk=org_pk)

    def render_to_response(self, context):
        return render(self.request, self.template_name, context)
