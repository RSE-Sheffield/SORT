__author__ = "Farhad Allian"

import django.urls
import django.contrib.auth.views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("login/", views.LoginInterfaceView.as_view(), name="login"),
    path("logout/", views.LogoutInterfaceView.as_view(), name="logout"),
    path("signup/", views.SignupView.as_view(), name="signup"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    # Change password using built-in authentication view
    # https://docs.djangoproject.com/en/5.2/topics/auth/default/#built-in-auth-views
    # https://docs.djangoproject.com/en/5.2/topics/auth/default/#django.contrib.auth.views.PasswordChangeView
    path("profile/change-password/",
         django.contrib.auth.views.PasswordChangeView.as_view(
             template_name="home/password_change_form.html",
             success_url=django.urls.reverse_lazy("profile"),
         ),
         name="password_change"),
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
    # path('password_reset/expired/', views.PasswordResetExpiredView.as_view(), name='password_reset_expired'),
    path("myorganisation/", views.MyOrganisationView.as_view(), name="myorganisation"),
    path(
        "organisation/create/",
        views.OrganisationCreateView.as_view(),
        name="organisation_create",
    ),
    # path("projects/create/", views.ProjectCreateView.as_view(), name="project_create"),
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
]
