__author__ = "Farhad Allian"

import django.urls
from django.urls import path, re_path

from . import views

urlpatterns = [
    path("", views.LandingView.as_view(), name="landing"),
    path("dashboard/", views.HomeView.as_view(), name="dashboard"),
    path("home/", views.HomeView.as_view(), name="home"),  # Backwards compatibility alias
    path("login/", views.LoginInterfaceView.as_view(), name="login"),
    path("logout/", views.LogoutInterfaceView.as_view(), name="logout"),
    re_path(
        r"^signup/(?P<key>\w+)/?$",
        views.SignupView.as_view(),
        name="signup",
    ),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    # Change password using built-in authentication view
    # https://docs.djangoproject.com/en/5.2/topics/auth/default/#built-in-auth-views
    # https://docs.djangoproject.com/en/5.2/topics/auth/default/#django.contrib.auth.views.PasswordChangeView
    path(
        "profile/change-password/",
        views.PasswordChangeView.as_view(
            template_name="home/password_change_form.html",
            success_url=django.urls.reverse_lazy("profile"),
        ),
        name="password_change",
    ),
    # Password reset by email (for lost passwords)
    path(
        "password_reset/",
        views.CustomPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        views.CustomPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        views.CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        views.CustomPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("myorganisation/", views.MyOrganisationView.as_view(), name="myorganisation"),
    path(
        "myorganisation/members/",
        views.OrganisationMembershipListView.as_view(),
        name="members",
    ),
    path(
        "myorganisation/members/delete/<int:pk>/",
        views.OrganisationMembershipDeleteView.as_view(),
        name="member_delete",
    ),
    path(
        "myorganisation/members/invite",
        views.MyOrganisationInviteView.as_view(),
        name="member_invite",
    ),
    re_path(
        r"^myorganisation/members/accept/(?P<key>\w+)/?$",
        views.MyOrganisationAcceptInviteView.as_view(),
        name="member_invite_accept",
    ),
    path(
        "myorganisation/data-sharing-agreement/",
        views.DataSharingAgreementView.as_view(),
        name="data_sharing_agreement",
    ),
    path(
        "organisation/create/",
        views.OrganisationCreateView.as_view(),
        name="organisation_create",
    ),
    path("projects/<int:project_id>/", views.ProjectView.as_view(), name="project"),
    path(
        "projects/create/<int:organisation_id>/",
        views.ProjectCreateView.as_view(),
        name="project_create",
    ),
    path(
        "projects/<int:project_id>/edit",
        views.ProjectEditView.as_view(),
        name="project_edit",
    ),
    path(
        "projects/<int:pk>/delete",
        views.ProjectDeleteView.as_view(),
        name="project_delete",
    ),
    path(
        "help/",
        views.HelpView.as_view(),
        name="help",
    ),
    path(
        "help/video-tutorial/",
        views.VideoTutorialView.as_view(),
        name="video_tutorial",
    ),
    path(
        "help/troubleshooting/",
        views.TroubleshootingView.as_view(),
        name="troubleshooting",
    ),
    path("help/faq/", views.FAQView.as_view(), name="faq", ),
    path("eula/", views.LicenseAgreementView.as_view(), name="eula"),
    path("privacy/", views.PrivacyPolicyView.as_view(), name="privacy"),
    path(
        "participant-information/",
        views.ParticipantInformationView.as_view(),
        name="participant_information",
    ),
    # Management console (staff only)
    path("console/", views.ConsoleView.as_view(), name="admin_dashboard"),
    path("console/organisations/", views.ConsoleOrganisationListView.as_view(), name="admin_organisations"),
    path("console/organisations/<int:pk>/", views.ConsoleOrganisationDetailView.as_view(), name="admin_organisation_detail"),
    path("console/projects/", views.ConsoleProjectListView.as_view(), name="admin_projects"),
    path("console/projects/<int:pk>/", views.ConsoleProjectDetailView.as_view(), name="admin_project_detail"),
    path("console/users/", views.ConsoleUserListView.as_view(), name="admin_users"),
    path("console/surveys/", views.ConsoleSurveyListView.as_view(), name="admin_surveys"),
    path("console/surveys/<int:pk>/", views.ConsoleSurveyDetailView.as_view(), name="admin_survey_detail"),
]
