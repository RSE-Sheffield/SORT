__author__ = "Farhad Allian"

from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("login/", views.LoginInterfaceView.as_view(), name="login"),
    path("logout/", views.LogoutInterfaceView.as_view(), name="logout"),
    path("signup/", views.SignupView.as_view(), name="signup"),
    path("", include("survey.urls"), name="survey"),
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
    path("projects/", views.ProjectListView.as_view(), name="projects"),
    # path("projects/create/", views.ProjectCreateView.as_view(), name="project_create"),
]
