"""
Views for the self-service organisation join request flow.

None of the requester-facing views use ``OrganisationRequiredMixin``: it
redirects anyone with no memberships to ``OrganisationGetStartedView``, and
these views are what that page sends the user on to.
"""

import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import FormView, ListView, TemplateView

from ..constants import ROLE_PROJECT_MANAGER, ROLES
from ..forms.join_request import JoinRequestForm
from ..forms.join_request_decision import (
    JoinRequestApprovalForm,
    JoinRequestRejectionForm,
)
from ..mixins import MemberManagementRequiredMixin, OrganisationRequiredMixin
from ..models import Organisation, OrganisationJoinRequest
from ..notifications import (
    notify_admins_of_join_request,
    notify_requester_of_join_decision,
)
from ..services import (
    AlreadyMemberError,
    DuplicateJoinRequestError,
    JoinRequestAlreadyDecidedError,
    organisation_join_request_service,
    organisation_service,
)

logger = logging.getLogger(__name__)

EMAIL_FAILED_MESSAGE = (
    "We could not send an email notification, but the request itself was saved."
)


class OrganisationGetStartedView(LoginRequiredMixin, TemplateView):
    """
    The landing page for a user who belongs to no organisation yet, offering
    both routes out of that state: join an existing organisation, or create a
    new one.

    ``OrganisationRequiredMixin`` redirects here rather than straight to
    ``organisation_create``, so a user who has already asked to join an
    organisation is told their request is waiting instead of being pushed
    towards creating a duplicate.
    """

    template_name = "organisation/join/get_started.html"

    def dispatch(self, request, *args, **kwargs):
        # A user who already has an organisation has no use for this page, and
        # everything on it is reachable from their organisation dashboard.
        # (No redirect loop: OrganisationRequiredMixin only bounces the users
        # this branch does not catch.)
        if request.user.is_authenticated and request.user.organisation_set.exists():
            return redirect("myorganisation")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pending_join_requests"] = (
            organisation_join_request_service.get_user_requests(self.request.user)
            .filter(status=OrganisationJoinRequest.Status.PENDING)
            .select_related("organisation")
        )
        return context


class OrganisationBrowseView(LoginRequiredMixin, ListView):
    """
    Browse and search the organisations already registered in SORT, so a user
    can ask to join theirs instead of creating a duplicate.
    """

    model = Organisation
    template_name = "organisation/join/browse.html"
    context_object_name = "organisations"
    paginate_by = 10

    def get_queryset(self):
        queryset = Organisation.objects.order_by("name")

        search_query = self.request.GET.get("q")
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query)
                | Q(description__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "member_organisation_ids": (
                    organisation_service.get_user_organisation_ids(self.request.user)
                ),
                "pending_organisation_ids": (
                    organisation_join_request_service.get_pending_organisation_ids(
                        self.request.user
                    )
                ),
                "current_search": self.request.GET.get("q", ""),
            }
        )
        return context


class JoinRequestCreateView(LoginRequiredMixin, FormView):
    """
    Confirm and submit a request to join one organisation.
    """

    form_class = JoinRequestForm
    template_name = "organisation/join/confirm.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.organisation = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        self.organisation = get_object_or_404(Organisation, pk=self.kwargs["pk"])

        # Report the states that make a request impossible before showing the
        # form, rather than letting the service raise on submission.
        if self.organisation.pk in organisation_service.get_user_organisation_ids(
            request.user
        ):
            messages.info(
                request, f"You are already a member of {self.organisation.name}."
            )
            return redirect("organisation_browse")

        pending_ids = organisation_join_request_service.get_pending_organisation_ids(
            request.user
        )
        if self.organisation.pk in pending_ids:
            messages.info(
                request,
                f"You already have a request to join {self.organisation.name} "
                "waiting for a decision.",
            )
            return redirect("join_requests_mine")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organisation"] = self.organisation
        return context

    def form_valid(self, form):
        try:
            join_request = organisation_join_request_service.create_join_request(
                user=self.request.user,
                organisation=self.organisation,
                message=form.cleaned_data["message"],
            )
        except (AlreadyMemberError, DuplicateJoinRequestError) as error:
            messages.info(self.request, str(error))
            return redirect("join_requests_mine")
        except PermissionDenied:
            messages.error(
                self.request,
                "You don't have permission to request to join this organisation.",
            )
            return redirect("organisation_browse")

        # Notify after the request has been committed: a failure to send must
        # not undo it. See home/notifications.py for the rationale.
        try:
            notify_admins_of_join_request(join_request, self.request)
        except Exception:
            logger.exception(
                "Failed to notify administrators of join request %s", join_request.pk
            )
            messages.warning(
                self.request,
                "Your request was submitted, but we could not email the "
                "administrators. They will still see it in SORT.",
            )

        messages.success(
            self.request,
            f"Your request to join {self.organisation.name} has been sent to its "
            "administrators.",
        )
        return redirect("join_requests_mine")


class MyJoinRequestListView(LoginRequiredMixin, ListView):
    """
    The requester's own join requests and their outcomes.
    """

    template_name = "organisation/join/mine.html"
    context_object_name = "join_requests"
    paginate_by = 10

    def get_queryset(self):
        return organisation_join_request_service.get_user_requests(self.request.user)


class JoinRequestWithdrawView(LoginRequiredMixin, View):
    """
    Withdraw one of the user's own pending requests, so they are not blocked
    from requesting a different organisation.
    """

    def post(self, request, *args, **kwargs):
        join_request = get_object_or_404(
            OrganisationJoinRequest.objects.select_related("organisation"),
            pk=self.kwargs["pk"],
            user=request.user,
        )

        try:
            organisation_join_request_service.withdraw(
                user=request.user, join_request=join_request
            )
        except JoinRequestAlreadyDecidedError:
            messages.info(request, "That request has already been decided.")
        else:
            messages.success(
                request,
                f"Your request to join {join_request.organisation.name} was "
                "withdrawn.",
            )

        return redirect("join_requests_mine")


class OrganisationJoinRequestListView(
    LoginRequiredMixin,
    MemberManagementRequiredMixin,
    OrganisationRequiredMixin,
    ListView,
):
    """
    An administrator's review queue for their organisation's join requests.
    """

    template_name = "organisation/members/join_requests.html"
    context_object_name = "join_requests"
    paginate_by = 20
    member_management_error_message = (
        "Only organisation administrators can review join requests."
    )

    @property
    def organisation(self) -> Organisation:
        return organisation_service.get_active_organisation(self.request)

    @property
    def show_all(self) -> bool:
        return self.request.GET.get("status") == "all"

    def get_queryset(self):
        return organisation_join_request_service.get_requests(
            user=self.request.user,
            organisation=self.organisation,
            status=None if self.show_all else OrganisationJoinRequest.Status.PENDING,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "organisation": self.organisation,
                # The role radios are rendered per row so each group can have
                # unique input ids; a single bound form instance would emit
                # duplicate ids across rows.
                "roles": ROLES,
                "default_role": ROLE_PROJECT_MANAGER,
                "show_all": self.show_all,
            }
        )
        return context


class JoinRequestDecisionView(
    LoginRequiredMixin, MemberManagementRequiredMixin, View
):
    """
    Base class for the approve and reject actions. POST only.
    """

    def get_join_request(self) -> OrganisationJoinRequest:
        if not hasattr(self, "_join_request"):
            self._join_request = get_object_or_404(
                OrganisationJoinRequest.objects.select_related("user", "organisation"),
                pk=self.kwargs["pk"],
            )
        return self._join_request

    def get_member_management_organisation(self, request):
        # Check permission against the organisation of the request being
        # decided, not the session's active organisation: otherwise an
        # administrator of one organisation could post another's request id.
        if not request.user.is_authenticated:
            return None
        return self.get_join_request().organisation

    def notify(self, join_request) -> None:
        try:
            notify_requester_of_join_decision(join_request, self.request)
        except Exception:
            logger.exception(
                "Failed to notify requester of decision on join request %s",
                join_request.pk,
            )
            messages.warning(self.request, EMAIL_FAILED_MESSAGE)

    def redirect_to_queue(self):
        return HttpResponseRedirect(reverse("join_requests"))


class JoinRequestApproveView(JoinRequestDecisionView):
    """
    Approve a join request, adding the requester with the chosen role.
    """

    def post(self, request, *args, **kwargs):
        join_request = self.get_join_request()
        form = JoinRequestApprovalForm(request.POST)

        if not form.is_valid():
            messages.error(request, "Please choose a valid role.")
            return self.redirect_to_queue()

        try:
            membership = organisation_join_request_service.approve(
                user=request.user,
                join_request=join_request,
                role=form.cleaned_data["role"],
            )
        except JoinRequestAlreadyDecidedError:
            messages.info(request, "That request has already been decided.")
            return self.redirect_to_queue()

        self.notify(join_request)
        messages.success(
            request,
            f"{join_request.user} has been added to "
            f"{join_request.organisation.name} as "
            f"{membership.get_role_display()}.",
        )
        return self.redirect_to_queue()


class JoinRequestRejectView(JoinRequestDecisionView):
    """
    Reject a join request. The requester may submit a new one later.
    """

    def post(self, request, *args, **kwargs):
        join_request = self.get_join_request()
        form = JoinRequestRejectionForm(request.POST)
        note = form.cleaned_data["note"] if form.is_valid() else ""

        try:
            organisation_join_request_service.reject(
                user=request.user, join_request=join_request, note=note
            )
        except JoinRequestAlreadyDecidedError:
            messages.info(request, "That request has already been decided.")
            return self.redirect_to_queue()

        self.notify(join_request)
        messages.success(
            request, f"The request from {join_request.user} was rejected."
        )
        return self.redirect_to_queue()
