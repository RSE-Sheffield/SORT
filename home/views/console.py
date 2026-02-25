"""
Staff management console.

This interface provides a dashboard overview of the app status. It's different from the /admin/ dashboard.
"""

from django.views.generic import TemplateView

from home.mixins import StaffRequiredMixin
from home.models import Organisation, Project, User
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
        context["organisations"] = Organisation.objects.order_by("name")
        return context


class ConsoleUserListView(StaffRequiredMixin, TemplateView):
    template_name = "console/users.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["users"] = User.objects.filter(is_active=True).order_by("last_name", "first_name")
        return context


class ConsoleSurveyListView(StaffRequiredMixin, TemplateView):
    template_name = "console/surveys.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["surveys"] = Survey.objects.select_related("project__organisation").order_by("-created_at")
        return context
