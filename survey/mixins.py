__author__ = "Farhad Allian"

from django.shortcuts import redirect
from survey.models import Invitation


class TokenAuthenticationMixin:

    def dispatch(self, request, *args, **kwargs):
        token = kwargs.get("token")
        if not self.is_valid_token(token):
            # If token is invalid, redirect to a custom error page or deny access
            return redirect("error_page")
        return super().dispatch(request, *args, **kwargs)

    def is_valid_token(self, token):

        return Invitation.objects.filter(token=token).exists()
