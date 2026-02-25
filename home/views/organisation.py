import django.http
import invitations.views
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView

from ..constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER
from ..forms.add_existing_member import AddExistingMemberForm
from ..forms.invite_member import InviteMemberForm
from ..mixins import OrganisationRequiredMixin
from ..models import Organisation, OrganisationMembership
from ..services import organisation_service, project_service


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
            return redirect("dashboard")


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
    LoginRequiredMixin, OrganisationRequiredMixin, TemplateView
):
    """
    Invite a new member to join an organisation via email,
    or add an existing user to the organisation.

    Handles two forms:
    1. InviteForm (from django-invitations) - for inviting new users
    2. AddExistingMemberForm - for adding existing users by email

    https://django-invitations.readthedocs.io/en/latest/usage.html
    """

    template_name = "organisation/members/create.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.organisation = organisation_service.get_user_organisation(request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Initialize both forms
        if "invite_form" not in context:
            context["invite_form"] = InviteMemberForm()

        if "add_existing_form" not in context:
            context["add_existing_form"] = AddExistingMemberForm(
                organisation=self.organisation, user=self.request.user
            )

        return context

    def post(self, request, *args, **kwargs):
        """Handle both invite and add existing user forms"""

        # Determine which form was submitted
        if "invite_submit" in request.POST:
            # Handle invite form (new user)
            invite_form = InviteMemberForm(request.POST)
            add_existing_form = AddExistingMemberForm(
                organisation=self.organisation, user=request.user
            )

            if invite_form.is_valid():
                email = invite_form.cleaned_data["email"]
                try:
                    invite = invite_form.save(email)
                    invite.inviter = request.user
                    invite.save()
                    invite.send_invitation(request)

                    messages.success(
                        request,
                        f"{email} has been invited to join the organisation. "
                        "They will receive an email with instructions.",
                    )
                    return redirect("member_invite")
                except Exception as e:
                    messages.error(request, f"Failed to send invitation: {str(e)}")

            return self.render_to_response(
                self.get_context_data(invite_form=invite_form, add_existing_form=add_existing_form)
            )

        elif "add_existing_submit" in request.POST:
            # Handle add existing user form
            invite_form = InviteMemberForm()
            add_existing_form = AddExistingMemberForm(
                request.POST, organisation=self.organisation, user=request.user
            )

            if add_existing_form.is_valid():
                user_to_add = add_existing_form.get_user()
                role = ROLE_PROJECT_MANAGER

                # Check if this is a duplicate (idempotent behavior)
                if hasattr(add_existing_form, "is_duplicate") and add_existing_form.is_duplicate:
                    messages.info(
                        request,
                        f"{user_to_add.email} is already a member of this organisation.",
                    )
                else:
                    # Add user to organisation
                    try:
                        organisation_service.add_user_to_organisation(
                            user=request.user,
                            user_to_add=user_to_add,
                            organisation=self.organisation,
                            role=role,
                        )
                        messages.success(
                            request,
                            f"{user_to_add.email} has been added to the organisation as a {role}.",
                        )
                    except Exception as e:
                        messages.error(request, f"Failed to add user: {str(e)}")

                return redirect("member_invite")

            return self.render_to_response(
                self.get_context_data(invite_form=invite_form, add_existing_form=add_existing_form)
            )

        # If neither submit button was pressed, show both forms
        return self.get(request, *args, **kwargs)


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


class DataSharingAgreementView(LoginRequiredMixin, DetailView):
    """
    Data Sharing Agreement between NHS organisations and University of Sheffield
    for research data sharing through SORT Online
    """

    model = Organisation
    template_name = "organisation/data_sharing_agreement.html"
    context_object_name = "organisation"

    def get_object(self, queryset=None):
        """
        Get the organisation and verify user has access to it.
        """

        organisation = self.request.user.organisation_set.first()

        # Verify user is a member of this organisation
        if not organisation_service.can_view(self.request.user, organisation):
            messages.error(
                self.request,
                "You don't have permission to view this organisation's data sharing agreement.",
            )
            return redirect("myorganisation")

        return organisation
