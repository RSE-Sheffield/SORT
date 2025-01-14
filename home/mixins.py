from django.shortcuts import redirect
from django.urls import reverse_lazy

from .models import User, Organisation

class OrganisationRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.organisation_set.count() > 0:
            return super().dispatch(request, *args, **kwargs)
        else:
            return redirect("organisation_create")

