from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect


class OrganisationRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.organisation_set.count() > 0:
            return super().dispatch(request, *args, **kwargs)
        else:
            return redirect("organisation_create")


class StaffRequiredMixin(UserPassesTestMixin):
    """Restrict access to staff members only."""

    def test_func(self):
        return self.request.user.is_active and self.request.user.is_staff
