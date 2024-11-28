from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic.edit import CreateView, UpdateView
from django.shortcuts import redirect
from survey.models import Questionnaire
from django.shortcuts import render
from django.views import View
from .forms import ManagerSignupForm, ManagerLoginForm, UserProfileForm
from django.contrib.auth import login
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import get_user_model

User = get_user_model()

class SignupView(CreateView):
    form_class = ManagerSignupForm
    template_name = 'home/register.html'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(reverse_lazy('home'))

class LogoutInterfaceView(LogoutView):
    success_url = reverse_lazy('login')

class LoginInterfaceView(LoginView):
    template_name = 'home/login.html'
    form_class = ManagerLoginForm
    success_url = reverse_lazy('home')

    def form_invalid(self, form):
        messages.error(self.request, "Invalid email or password.")
        return super().form_invalid(form)

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
        messages.success(self.request, 'Your profile has been successfully updated.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'There was an error updating your profile. Please try again.')
        return super().form_invalid(form)


class CustomPasswordResetView(PasswordResetView):
    template_name = 'home/password_reset_form.html'
    email_template_name = 'home/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')
    subject_template_name = 'home/password_reset_subject.txt'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'home/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'home/password_reset_done.html'


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'home/password_reset_complete.html'

# class PasswordResetExpiredView(TemplateView):  # leave for now
#     template_name = 'home/password_reset_expired.html'
