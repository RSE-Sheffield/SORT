from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect

from .services import organisation_service


class OrganisationRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.organisation_set.count() > 0:
            return super().dispatch(request, *args, **kwargs)
        else:
            return redirect("organisation_create")


class MemberManagementRequiredMixin:
    """Restrict member-management actions to organisation administrators.

    Without this guard a non-admin could trigger an action whose service-layer
    permission check raises PermissionDenied and surfaces as a 500.
    """

    member_management_error_message = (
        "Only organisation administrators can manage members."
    )

    def get_member_management_organisation(self, request):
        # Default: the user's primary organisation.
        return organisation_service.get_user_organisation(request.user)

    def dispatch(self, request, *args, **kwargs):
        organisation = self.get_member_management_organisation(request)
        if (
            request.user.is_authenticated
            and organisation
            and not organisation_service.can_manage_members(request.user, organisation)
        ):
            messages.error(request, self.member_management_error_message)
            return redirect("members")
        return super().dispatch(request, *args, **kwargs)


class StaffRequiredMixin(UserPassesTestMixin):
    """Restrict access to staff members only."""

    def test_func(self):
        return self.request.user.is_active and self.request.user.is_staff
