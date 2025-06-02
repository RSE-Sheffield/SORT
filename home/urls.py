__author__ = "Farhad Allian"

from django.urls import path

from . import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
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
