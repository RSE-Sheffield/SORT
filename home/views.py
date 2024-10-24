from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic.edit import CreateView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from survey.models import Questionnaire
from django.shortcuts import render
from django.views import View
from .forms import ManagerSignupForm

class SignupView(CreateView):
    form_class = ManagerSignupForm
    template_name = 'home/register.html'
    success_url = reverse_lazy('home')

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect(reverse_lazy('notes.list'))
        return super().get(request, *args, **kwargs)

class LogoutInterfaceView(LogoutView):
    success_url = reverse_lazy('login')

class LoginInterfaceView(LoginView):
    template_name = 'home/login.html'
    success_url = reverse_lazy('home')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class HomeView(LoginRequiredMixin, View):
    template_name = 'home/welcome.html'
    login_url = 'login'
    def get(self, request):
        consent_questionnaire = Questionnaire.objects.get(
            title="Consent")
        return render(request, 'home/welcome.html', {'questionnaire': consent_questionnaire})
