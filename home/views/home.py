from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import TemplateView

from ..services import project_service


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
