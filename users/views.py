from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView, PasswordChangeDoneView
from django.urls import reverse_lazy
from .forms import LoginForm, RegisterForm, UpdateUserForm, UpdateProfileForm

from django.views import View
from django.contrib import messages

from django.contrib.messages.views import SuccessMessageMixin

from django.conf import settings
from django.utils.translation import gettext as _

class RegisterView(View):
    form_class = RegisterForm
    initial = {'key': 'value'}
    template_name = 'registration/register.html'

    def dispatch(self, request, *args, **kwargs):
        return super(RegisterView, self).dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwards):
        form = self.form_class(initial = self.initial)
        return render(request, self.template_name, {'form':form})
    
    def post(self, request, *args, **kwards):
        form = self.form_class(request.POST)

        if form.is_valid():
            form.save()

            username = form.cleaned_data.get('username')
            messages.success(request, _('Account created'))

            return redirect(to='login')
        
        return render(request, self.template_name, {'form': form})


def home(request):
    return render(request, 'registration/home.html')
 

class CustomLoginView(LoginView):
    form_class = LoginForm

    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me')

        if not remember_me:
            # set session expiry to 0 seconds.
            self.request.session.set_expiry(0)

            # Set session as modified to update data/cookie
            self.request.session.modified = True

        return super(CustomLoginView, self).form_valid(form)
    

class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = 'registration/password_reset.html'
    email_template = 'registration/password_reset_email.html'

    subject_template_name = 'registration/password_reset_subject'

    success_message = _("""
                        We have emailed you instructions for setting your password, 
                        if an account exists with the email you entered. You should receive them shortly.
                        If you don't recieve an email,
                        please make sure you've entered the address you registered with, and check your spam folder.
                        """)
    success_url = reverse_lazy('login')


class ChangePasswordView(SuccessMessageMixin, PasswordChangeView):
    template_name = 'registration/change_password.html'
    success_message = _("Successfully changed your password")