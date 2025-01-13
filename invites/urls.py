from django.urls import path

from .views import InvitationView, SuccessInvitationView

urlpatterns = [
    path("", InvitationView.as_view(), name="invite"),
    path("success/", SuccessInvitationView.as_view(), name="success_invitation"),
]
