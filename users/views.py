from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView
from django.contrib.auth import logout as user_logout
from django.urls import reverse_lazy
from .forms import LoginForm, RegisterForm, UpdateUserForm, UpdateProfileForm

from django.views import View
from django.contrib import messages

from django.contrib.messages.views import SuccessMessageMixin

from django.conf import settings
from django.utils.translation import gettext as _



class RegisterView(View):
    """View for user registration
       url: 'register/'
    """
    form_class = RegisterForm
    initial = {'key': 'value'}
    template_name = 'registration/register.html'

    def dispatch(self, request, *args, **kwargs):
        return super(RegisterView, self).dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwards):
        """Function to display the registration form

        Args:
            request (HttpRequest): request object
        """
        form = self.form_class(initial = self.initial)
        return render(request, self.template_name, {'form':form})
    
    def post(self, request, *args, **kwards):
        """Function to process the submitted form data

        Args:
            request (HttpRequest): request object
        """
        form = self.form_class(request.POST)
        # checking form validity
        if form.is_valid():
            # saving the user data 
            form.save()
            username = form.cleaned_data.get('username')
            # success message
            messages.success(request, _('Account created'))
            return redirect(to='login')
        # returning to the form in case of invalid form
        return render(request, self.template_name, {'form': form})


def home(request):
    """Displays the home page
       url: '/'

    Args:
        request (HttpRequest): request object
    """
    return render(request, 'registration/home.html')
 

def logout(request):
    """Logout the user and redirects to login page
       url: '/logout'

    Args:
        request (HttpRequest): request object
    """
    user_logout(request)
    return redirect('login')

def change_language(request, lang_code):
    """Change user language for translation.
       url: '/change_lang'

    Args:
        request (HttpRequest): request object
        lang_code(str): language code
    """
    next = request.META.get('HTTP_REFERER')
    translation.activate(lang_code)
    response = HttpResponse(status=204)
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code)
    return response

class CustomLoginView(LoginView):
    """View to display and process user's login
       url:'/login'

    Args:
        LoginView: Django's LoginView
    """
    form_class = LoginForm

    def get_success_url(self):
        """Redirect users based on their is_staff status. This status differentiate teachers from students.

        """
        user = self.request.user
        if user.is_staff:
            return '/session/list'
        else:
            return '/session/enter'
        

    def form_valid(self, form):
        """Function extending the functionality of validity check
           url:'/login'

        Args:
            form (LoginForm): submitted login form data

        """
        # user's input for remember_me checkbox
        remember_me = form.cleaned_data.get('remember_me')

        if not remember_me:
            # set session expiry to 0 seconds.
            self.request.session.set_expiry(0)

            # Set session as modified to update data/cookie
            self.request.session.modified = True

        return super(CustomLoginView, self).form_valid(form)
    

class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    """This view uses Django PasswordResetView to allow uses to change their password.
    This view initiates the password change process.
    
    """
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
    """This view displays the form to change the password and process the submission.

    """
    template_name = 'registration/change_password.html'
    success_message = _("Successfully changed your password")