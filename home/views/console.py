"""
Staff management console.

This interface provides a dashboard overview of the app status. It's different from the /admin/ dashboard.
"""

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, View
from django.views.generic.base import TemplateResponseMixin

from home.constants import DELETED_ACCOUNT_EMAIL_DOMAIN
from home.forms.user_profile import UserProfileForm
from home.mixins import StaffRequiredMixin
from home.models import (
    DataProtectionEvent,
    Organisation,
    OrganisationJoinRequest,
    OrganisationMembership,
    Project,
    User,
)
from home.services import data_protection_service, user_service
from home.services.analytics import CSV_REPORTS, DEFAULT_ACTIVE_DAYS, UsageAnalytics
from home.services.organisation import remove_membership_and_record_event
from home.views.sorting import SortableMixin
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


# Bounds for the "active in the last N days" window on the analytics page
MAX_ACTIVE_DAYS = 3650


def get_active_days(request) -> int:
    """Parse the ?days= query parameter, falling back to the default when missing or invalid."""
    try:
        days = int(request.GET.get("days", DEFAULT_ACTIVE_DAYS))
    except ValueError:
        return DEFAULT_ACTIVE_DAYS
    return min(max(days, 1), MAX_ACTIVE_DAYS)


class ConsoleAnalyticsView(StaffRequiredMixin, TemplateView):
    """
    Usage analytics for impact reporting: headline figures, leaderboards and trends over time.
    """

    template_name = "console/analytics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        analytics = UsageAnalytics(active_days=get_active_days(self.request))
        context["analytics"] = analytics.as_dict()
        context["csv_reports"] = CSV_REPORTS
        return context


class ConsoleAnalyticsExportView(StaffRequiredMixin, View):
    """
    Download one of the usage analytics tables as CSV.
    """

    def get(self, request):
        report = request.GET.get("report", "surveys")
        if report not in CSV_REPORTS:
            return HttpResponse(f"Unknown report '{report}'", status=400, content_type="text/plain")
        analytics = UsageAnalytics(active_days=get_active_days(request))
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename=sort_usage_{report}.csv"
        analytics.write_csv(report, response)
        return response


class ConsoleOrganisationListView(StaffRequiredMixin, SortableMixin, TemplateView):
    template_name = "console/organisations.html"
    sort_fields = {
        "name": "name",
        "members": "members_count",
        "projects": "project_count",
        "surveys": "survey_count",
        "responses": "response_count",
        "created": "created_at",
    }
    default_sort = "name"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organisations = Organisation.objects.annotate(
            members_count=Count("organisationmembership", distinct=True),
            project_count=Count("projects", distinct=True),
            survey_count=Count("projects__survey", distinct=True),
            response_count=Count("projects__survey__survey_response", distinct=True),
        )
        context["organisations"] = self.apply_sort(organisations, context)
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
        # Queried directly rather than via organisation_join_request_service:
        # that service's get_requests() requires manage_members permission on
        # the organisation, which staff viewing the console may not hold —
        # StaffRequiredMixin above is the only gate this page needs.
        context["join_requests"] = OrganisationJoinRequest.objects.filter(
            organisation=org
        ).select_related("user", "decided_by")
        return context


class ConsoleUserListView(StaffRequiredMixin, SortableMixin, TemplateView):
    template_name = "console/users.html"
    sort_fields = {
        "name": ("last_name", "first_name"),
        "email": "email",
        "status": "is_active",
        "organisations": "organisation_count",
        "joined": "date_joined",
    }
    default_sort = "name"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        status = self.request.GET.get("status", "active")
        qs = User.objects.annotate(organisation_count=Count("organisationmembership"))
        deleted_filter = {"email__endswith": f"@{DELETED_ACCOUNT_EMAIL_DOMAIN}"}
        if status == "deleted":
            qs = qs.filter(**deleted_filter)
        elif status == "suspended":
            qs = qs.filter(is_active=False).exclude(**deleted_filter)
        elif status == "all":
            pass
        else:
            status = "active"
            qs = qs.exclude(**deleted_filter)
        context["users"] = self.apply_sort(qs, context)
        context["status_filter"] = status
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


class ConsoleProjectListView(StaffRequiredMixin, SortableMixin, TemplateView):
    template_name = "console/projects.html"
    sort_fields = {
        "name": "name",
        "organisation": ("organisation__name", "name"),
        "surveys": "survey_count",
        "responses": "response_count",
        "created": "created_at",
    }
    default_sort = "organisation"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org_id = self.request.GET.get("organisation")
        projects = Project.objects.select_related("organisation").annotate(
            survey_count=Count("survey", distinct=True),
            response_count=Count("survey__survey_response", distinct=True),
        )
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
        context["projects"] = self.apply_sort(projects, context)
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


class ConsoleSurveyListView(StaffRequiredMixin, SortableMixin, TemplateView):
    template_name = "console/surveys.html"
    sort_fields = {
        "name": "name",
        "project": "project__name",
        "organisation": "project__organisation__name",
        "responses": "response_count",
        "created": "created_at",
    }
    default_sort = "created"
    default_dir = "desc"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org_id = self.request.GET.get("organisation")
        project_id = self.request.GET.get("project")

        surveys = Survey.objects.select_related("project__organisation").annotate(
            response_count=Count("survey_response")
        )

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

        context["surveys"] = self.apply_sort(surveys, context)
        context["organisations"] = Organisation.objects.order_by("name")
        # Projects dropdown: scoped to selected org if present, otherwise all
        projects = Project.objects.select_related("organisation").order_by("organisation__name", "name")
        if org_id:
            projects = projects.filter(organisation_id=org_id)
        context["projects"] = projects
        return context


class ConsoleDeleteUserView(StaffRequiredMixin, TemplateResponseMixin, View):
    template_name = "console/delete_user_confirm.html"

    def _get_user(self, pk):
        return get_object_or_404(User, pk=pk, is_active=True)

    def _check_safe(self, request, target_user):
        if target_user == request.user or target_user.is_staff or target_user.is_superuser:
            raise PermissionDenied

    def get(self, request, pk):
        target_user = self._get_user(pk)
        self._check_safe(request, target_user)
        return self.render_to_response({"viewed_user": target_user})

    def post(self, request, pk):
        target_user = self._get_user(pk)
        self._check_safe(request, target_user)
        display_name = str(target_user)
        user_service.anonymise(target_user)
        messages.success(request, f"{display_name} has been anonymised and removed.")
        return redirect("admin_users")


class ConsoleExportUserDataView(StaffRequiredMixin, TemplateResponseMixin, View):
    """
    Generate a UK GDPR Article 15 subject access export for a user (issue #582).
    """

    template_name = "console/export_user_data_confirm.html"

    def _get_exportable_user(self, pk):
        user = get_object_or_404(User, pk=pk)
        if user.is_deleted:
            raise PermissionDenied("This account has been erased and has no personal data to export.")
        return user

    def get(self, request, pk):
        return self.render_to_response({"viewed_user": self._get_exportable_user(pk)})

    def post(self, request, pk):
        target_user = self._get_exportable_user(pk)

        data = user_service.export_personal_data(target_user)
        data["data_protection_history"] = [
            {
                "event_type": event.get_event_type_display(),
                "notes": event.notes,
                "actioned_at": event.actioned_at,
                "requested_at": event.requested_at,
            }
            for event in data_protection_service.list_events(
                request.user, subject_user_id=target_user.pk
            )
        ]

        data_protection_service.record_event(
            event_type=DataProtectionEvent.EventType.EXPORT,
            subject_user=target_user,
            actioned_by=request.user,
            notes="Subject access data exported via staff console",
        )

        response = JsonResponse(data, json_dumps_params={"indent": 2})
        response["Content-Disposition"] = f'attachment; filename="sar-export-user-{target_user.pk}.json"'
        return response


class ConsoleRemoveMemberView(StaffRequiredMixin, TemplateResponseMixin, View):
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
        user_display = str(membership.user)
        org_name = org.name
        try:
            remove_membership_and_record_event(
                OrganisationMembership.objects.filter(
                    pk=membership_pk, organisation=org
                ),
                actioned_by=request.user,
                notes=f"Removed from organisation '{org_name}'",
            )
        except OrganisationMembership.DoesNotExist:
            pass  # already removed by a concurrent request; end state is correct
        messages.success(request, f"{user_display} removed from {org_name}.")
        return redirect("admin_organisation_detail", pk=org_pk)


class ConsoleSuspendUserView(StaffRequiredMixin, TemplateResponseMixin, View):
    """
    Suspend a user account (UK GDPR Article 18, Right to Restriction).

    Sets ``is_active = False`` so the user can no longer log in. No data is
    deleted and the action is reversible via :class:`ConsoleUnsuspendUserView`.
    """

    template_name = "console/suspend_user_confirm.html"

    def _get_suspendable_user(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        # Guard against locking out yourself, a fellow staff member, or a
        # superuser, and against suspending an already-anonymised (deleted)
        # account.
        if user == request.user or user.is_staff or user.is_superuser or user.is_deleted:
            raise PermissionDenied("This account cannot be suspended.")
        return user

    def get(self, request, pk):
        user = self._get_suspendable_user(request, pk)
        return self.render_to_response({"viewed_user": user})

    def post(self, request, pk):
        user = self._get_suspendable_user(request, pk)
        user.is_active = False
        user.save(update_fields=["is_active"])
        messages.success(request, f"{user} has been suspended.")
        return redirect("admin_user_detail", pk=pk)


class ConsoleUnsuspendUserView(StaffRequiredMixin, View):
    """Lift the suspension on a user account, restoring login access."""

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user.is_deleted:
            raise PermissionDenied("This account has been deleted and cannot be reactivated.")
        user.is_active = True
        user.save(update_fields=["is_active"])
        messages.success(request, f"The suspension on {user} has been lifted.")
        return redirect("admin_user_detail", pk=pk)


class ConsoleEditUserView(StaffRequiredMixin, TemplateResponseMixin, View):
    """
    Let staff correct a user's name/email on their behalf (UK GDPR Art. 16,
    Right to Rectification — issue #695). Used when a correction request
    arrives by phone/email rather than via the user's own profile page.

    Email changes take effect immediately without re-verification: staff
    have already verified the requester's identity and the new address
    off-platform before making this change.
    """

    template_name = "console/edit_user.html"

    def _get_user(self, pk):
        return get_object_or_404(User, pk=pk)

    def get(self, request, pk):
        target_user = self._get_user(pk)
        form = UserProfileForm(instance=target_user)
        return self.render_to_response({"viewed_user": target_user, "form": form})

    def post(self, request, pk):
        target_user = self._get_user(pk)
        old_values = {
            "first_name": target_user.first_name,
            "last_name": target_user.last_name,
            "email": target_user.email,
        }
        form = UserProfileForm(request.POST, instance=target_user)
        if not form.is_valid():
            return self.render_to_response({"viewed_user": target_user, "form": form})

        changes = []
        for field, label in (
            ("first_name", "First name"),
            ("last_name", "Last name"),
            ("email", "Email"),
        ):
            old, new = old_values[field], form.cleaned_data[field]
            if old != new:
                changes.append(f"{label}: '{old}' -> '{new}'")

        if not changes:
            messages.info(request, "No changes were made.")
            return redirect("admin_user_detail", pk=pk)

        user_service.update_user(
            target_user,
            first_name=form.cleaned_data["first_name"],
            last_name=form.cleaned_data["last_name"],
            email=form.cleaned_data["email"],
        )
        data_protection_service.record_event(
            event_type=DataProtectionEvent.EventType.RECTIFICATION,
            subject_user=target_user,
            actioned_by=request.user,
            notes="Corrected by staff via console: " + "; ".join(changes),
        )
        messages.success(request, f"{target_user}'s details have been updated.")
        return redirect("admin_user_detail", pk=pk)


class ConsoleDataProtectionLogView(StaffRequiredMixin, SortableMixin, TemplateView):
    template_name = "console/data_protection_log.html"
    sort_fields = {
        "when": "actioned_at",
        "event": "event_type",
        "subject": "subject_identifier",
        "actioned_by": "actioned_by__email",
        "requested_by": "requested_by__email",
    }
    default_sort = "when"
    default_dir = "desc"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event_type = self.request.GET.get("event_type") or None
        raw_subject = self.request.GET.get("subject_user") or None
        try:
            subject_user_id = int(raw_subject) if raw_subject else None
        except (TypeError, ValueError):
            subject_user_id = None

        events = data_protection_service.list_events(
            self.request.user,
            event_type=event_type,
            subject_user_id=subject_user_id,
        )

        events = self.apply_sort(events, context)
        paginator = Paginator(events, 25)
        page_number = self.request.GET.get("page") or 1
        page = paginator.get_page(page_number)

        filter_params = self.request.GET.copy()
        filter_params.pop("page", None)

        context["events"] = page
        context["page_obj"] = page
        context["paginator"] = paginator
        context["event_types"] = DataProtectionEvent.EventType.choices
        context["selected_event_type"] = event_type
        context["selected_subject_user"] = raw_subject
        context["filter_qs"] = filter_params.urlencode()
        return context
