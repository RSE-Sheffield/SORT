from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect
from django.urls import reverse_lazy
from survey.models import Questionnaire
from django.shortcuts import render
from django.views import View

class SignupView(CreateView):
    form_class = UserCreationForm
    template_name = 'home/register.html'
    success_url = reverse_lazy('home')

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect(reverse_lazy('notes.list'))
        return super().get(request, *args, **kwargs)

class LogoutInterfaceView(LogoutView):
    template_name = 'home/logout.html'

class LoginInterfaceView(LoginView):
    template_name = 'home/login.html'
    success_url = reverse_lazy('home')


class HomeView(LoginRequiredMixin, View):
    template_name = 'home/welcome.html'
    login_url = 'login'
    def get(self, request):
        consent_questionnaire = Questionnaire.objects.get(
            title="Consent")
        return render(request, 'home/welcome.html', {'questionnaire': consent_questionnaire})
