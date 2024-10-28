from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from survey.models import Questionnaire
from django.shortcuts import render
from django.views import View
from .forms import ManagerSignupForm, ManagerLoginForm, UserProfileForm
from django.contrib.auth import authenticate, login
from django.contrib import messages

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
    form_class = ManagerLoginForm
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        email = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')

        user = authenticate(request=self.request, username=email, password=password)
        if user is not None:
            login(self.request, user)
            return super().form_valid(form)
        else:
            messages.error(self.request, "Invalid email or password.")
            return self.form_invalid(form)

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

class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'home/profile.html'
    success_url = reverse_lazy('profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        form.save()  # Save the user's updated information
        messages.success(self.request, 'Your profile was successfully updated!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)