from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic.edit import CreateView, UpdateView
from django.shortcuts import redirect
from survey.models import Questionnaire
from django.shortcuts import render
from django.views import View
from .forms import ManagerSignupForm, ManagerLoginForm, UserProfileForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import send_mail

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
        form.save()  # Save the user's updated information
        messages.success(self.request, 'Your profile was successfully updated!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


class CustomPasswordResetView(PasswordResetView):
    template_name = 'home/password_reset_form.html'
    email_template_name = 'home/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')
    subject_template_name = 'home/password_reset_subject.txt'

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        if not email:
            messages.error(request, "Email field is required.")
            return self.get(request, *args, **kwargs)

        return super().post(request, *args, **kwargs)

    def form_valid(self, form):

        response = super().form_valid(form)

        for user in form.get_users(form.cleaned_data['email']):
            custom_uid = urlsafe_base64_encode(force_bytes(user.pk, encoding='utf-16'))
            custom_token = default_token_generator.make_token(user)

            context = {
                'uid': custom_uid,
                'token': custom_token,
                'first_name': user.first_name,
                'username': user.username,
                'protocol': 'https' if self.request.is_secure() else 'http',
                'domain': self.request.get_host(),
            }
            email_subject = render_to_string(self.subject_template_name, context).strip()
            email_body = render_to_string(self.email_template_name, context)

            send_mail(
                subject=email_subject,
                message=email_body,
                from_email="no-reply-SORT@sheffield.ac.uk",
                recipient_list=[user.email],
            )

        return super().form_valid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'home/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'home/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')



class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'home/password_reset_complete.html'
