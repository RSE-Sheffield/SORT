from typing import Optional

import django.contrib.auth.views
import django.http
import invitations.models
import invitations.views
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from survey.models import Survey
from survey.services import survey_service

from .constants import ROLE_ADMIN, ROLE_PROJECT_MANAGER
from .forms.add_existing_member import AddExistingMemberForm
from .forms.invite_member import InviteMemberForm
from .forms.manager_login import ManagerLoginForm
from .forms.manager_signup import ManagerSignupForm
from .forms.organisation_invite import OrganisationInviteForm
from .forms.user_profile import UserProfileForm
from .mixins import OrganisationRequiredMixin
from .models import Organisation, OrganisationMembership, Project
from .services import organisation_service, project_service

User = get_user_model()


class SignupView(CreateView):
    form_class = ManagerSignupForm
    template_name = "home/register.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._invitation: Optional[invitations.models.Invitation] = None

    @property
    def invitation(self) -> invitations.models.Invitation:
        """
        The user invite that was emailed to the new user. Each
        invitation is uniquely identified by its secret key and email address.
        """
        if self._invitation is None:
            try:
                self._invitation = invitations.models.Invitation.objects.get(
                    key=self.kwargs["key"]
                )
            # This signup must have an invitation
            except invitations.models.Invitation.DoesNotExist:
                raise PermissionDenied("You must be invited to sign up.")
        return self._invitation

    def get_context_data(self, **context):
        context = super().get_context_data(**context)

        # The invited user will be invited to the same organisation
        # as the manager who invited them.
        context["organisation"] = organisation_service.get_user_organisation(
            self.invitation.inviter
        )
        context["email"] = self.invitation.email

        return context

    def get_initial(self):
        initial = super().get_initial()
        initial["key"] = self.invitation.key
        return initial

    def form_valid(self, form):
        user = form.save()
        login(self.request, user, backend="django.contrib.auth.backends.ModelBackend")
        return redirect(reverse_lazy("dashboard"))


class LandingView(TemplateView):
    """
    Public landing page for new visitors arriving from sort-online.org.
    Redirects authenticated users to their dashboard.
    """

    template_name = "home/landing.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)


class LogoutInterfaceView(LogoutView):
    success_url = reverse_lazy("landing")


class LoginInterfaceView(LoginView):
    template_name = "home/login.html"
    form_class = ManagerLoginForm
    success_url = reverse_lazy("dashboard")

    def form_invalid(self, form):
        messages.error(self.request, "Invalid email or password.")
        return super().form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Handle successful login and process any pending invitation."""
        response = super().form_valid(form)

        # Check if there's an invitation key in the request
        invitation_key = self.request.GET.get("invitation_key") or self.request.POST.get(
            "invitation_key"
        )

        if invitation_key:
            try:
                invitation = invitations.models.Invitation.objects.get(key=invitation_key)

                # Verify the invitation is for this user's email
                if invitation.email.lower() == self.request.user.email.lower():
                    # Check if invitation is still valid and not already accepted
                    if not invitation.accepted and not invitation.key_expired():
                        # Get the inviter's organisation
                        inviter_organisation = organisation_service.get_user_organisation(
                            invitation.inviter
                        )

                        # Check if user is not already a member
                        existing_membership = OrganisationMembership.objects.filter(
                            user=self.request.user, organisation=inviter_organisation
                        ).first()

                        if not existing_membership:
                            # Add user to the organisation
                            organisation_service.add_user_to_organisation(
                                user=invitation.inviter,
                                user_to_add=self.request.user,
                                organisation=inviter_organisation,
                                role=ROLE_PROJECT_MANAGER,
                            )

                            # Mark invitation as accepted
                            invitation.accepted = True
                            invitation.save()

                            messages.success(
                                self.request,
                                f"You have been added to {inviter_organisation.name}.",
                            )
                        else:
                            messages.info(
                                self.request,
                                f"You are already a member of {inviter_organisation.name}.",
                            )
                    elif invitation.accepted:
                        messages.info(self.request, "This invitation has already been accepted.")
                    else:
                        messages.error(self.request, "This invitation has expired.")
                else:
                    messages.error(
                        self.request,
                        "This invitation is for a different email address.",
                    )
            except invitations.models.Invitation.DoesNotExist:
                messages.error(self.request, "Invalid invitation.")

        return response


class HomeView(LoginRequiredMixin, View):
    """
    Dashboard view for authenticated users showing their projects.
    """

    template_name = "home/welcome.html"
    context_object_name = "projects"

    def get(self, request):
        user = self.request.user
        # all projects for current user
        projects = project_service.get_user_projects(user)
        return render(request, self.template_name, context=dict(projects=projects))


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = "home/profile.html"
    success_url = reverse_lazy("profile")

    def get_object(self, queryset=None) -> User:
        """
        Get the current user.
        """
        # We only ever want to be able to retrieve the authenticated user
        if queryset is not None:
            raise ValueError("queryset is not None")
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Your profile has been successfully updated.")
        return super().form_valid(form)

    def form_invalid(self, form):
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


class PasswordChangeView(django.contrib.auth.views.PasswordChangeView):
    def form_valid(self, form):
        messages.success(self.request, "Your password has been changed.")
        return super().form_valid(form=form)


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

    Supports inviting both new users and existing SORT users.

    https://django-invitations.readthedocs.io/en/latest/usage.html
    """

    template_name = "organisation/members/create.html"
    form_class = OrganisationInviteForm

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

    Routes existing users to login and new users to signup.
    """

    def post(self, *args, **kwargs):
        import django.urls

        try:
            super().post(*args, **kwargs)
        # There is no public signup URL
        except django.urls.NoReverseMatch:
            pass

        # Check if a user with this email already exists
        invitation = self.object
        existing_user = User.objects.filter(email__iexact=invitation.email).first()

        if existing_user:
            # User already exists - send them to login with the invitation key
            return redirect(f"{reverse('login')}?invitation_key={invitation.key}")
        else:
            # New user - send them to signup with the invitation key
            return redirect("signup", key=invitation.key)


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


class HelpView(TemplateView):
    """
    User guide
    """

    template_name = "help/index.html"


class VideoTutorialView(TemplateView):
    """
    Beginner's intro video.
    """

    template_name = "help/video-tutorial.html"


class TroubleshootingView(TemplateView):
    template_name = "help/troubleshooting.html"


class FAQView(TemplateView):
    """
    Frequently asked questions (FAQs)
    """

    template_name = "help/faq.html"


class LicenseAgreementView(TemplateView):
    """
    End user license agreement
    """

    template_name = "about/end_user_license_agreement.html"


class PrivacyPolicyView(TemplateView):
    """
    Privacy policy and data protection notice
    """

    template_name = "about/privacy.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_date"] = timezone.now().strftime("%d %B %Y")
        return context


class ParticipantInformationView(TemplateView):
    """
    Participant information sheet for research study
    """

    template_name = "about/participant_information.html"


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
