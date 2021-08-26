from django.contrib.auth.views import (LoginView, LogoutView,
                                       PasswordChangeDoneView,
                                       PasswordChangeView,
                                       PasswordResetCompleteView,
                                       PasswordResetConfirmView,
                                       PasswordResetDoneView,
                                       PasswordResetView)
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:main')
    template_name = 'users/signup.html'


class ChangePassword(PasswordChangeView):
    template_name = 'users/password_change_form.html'
    success_url = reverse_lazy('password_change_done')


class ChangePasswordDone(PasswordChangeDoneView):
    template_name = 'users/password_change_done.html'


class ResetPassword(PasswordResetView):
    template_name = 'users/password_reset_form.html'
    success_url = reverse_lazy('password_reset_done')


class ResetPasswordDone(PasswordResetDoneView):
    template_name = 'users/password_reset_done.html'


class ResetPasswordConfirm(PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('password_confirm_done')


class ResetPasswordConfirmDone(PasswordResetCompleteView):
    template_name = 'users/password_reset_complete.html'


class Login(LoginView):
    template_name = 'users/login.html'
    success_url = reverse_lazy('posts:main')


class Logout(LogoutView):
    template_name = 'users/logged_out.html'
