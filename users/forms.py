from django import forms
from django.utils.translation import gettext as _
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Profile

class RegisterForm(UserCreationForm):
    """Thif form uses Django's UserCreationForm to render registration form.

    """
    first_name = forms.CharField(max_length=100,
                                 required=True,
                                 widget=forms.TextInput(attrs={
                                     'placeholder': _('first name'),
                                     'class': 'form-control',
                                 }))
    last_name = forms.CharField(max_length=100,
                                required=True,
                                widget=forms.TextInput(attrs={
                                    'placeholder': _('last name'),
                                    'class': 'form-control'
                                }))
    username = forms.CharField(max_length=100,
                                required=True,
                                widget=forms.TextInput(attrs={
                                    'placeholder': _('user name'),
                                    'class': 'form-control'
                                }))
    email = forms.EmailField(required=True,
                             widget=forms.EmailInput(attrs={
                                 'placeholder': _('email'),
                                 'class': 'form-control'
                             }))   
    password1 = forms.CharField(required=True,
                                widget=forms.PasswordInput(attrs={
                                    'placeholder': _('password'),
                                    'class': 'form-control',
                                }))   
    password2 = forms.CharField(required=True,
                                widget=forms.PasswordInput(attrs={
                                    'placeholder': _('password'),
                                    'class': 'form-control',
                                }))
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']


class LoginForm(AuthenticationForm):
    """This form uses Django's AuthenticationForm to render login form.

    """
    username = forms.CharField(max_length=100,
                               required=True,
                               widget=forms.TextInput(attrs={
                                   'placeholder': _('user name'),
                                   'class': 'form-control'
                               })) 
    password = forms.CharField(required=True,
                               widget= forms.PasswordInput(attrs={
                                   'placeholder': _('enter password'),
                                   'name': 'password',
                                   'class':'form-control'
                               }))
    remember_me = forms.BooleanField(required= False)
    class Meta:
        model = User
        fields = ['username','password','remember_me']


class UpdateUserForm(forms.ModelForm):
    """This form prepares user update form.

    """
    first_name = forms.CharField(max_length=100,
                                 required=True,
                                 widget=forms.TextInput(attrs={
                                     'placeholder': _('first name'),
                                     'class': 'form-control',
                                 }))
    
    last_name = forms.CharField(max_length=100,
                                required=True,
                                widget=forms.TextInput(attrs={
                                    'placeholder': _('last name'),
                                    'class': 'form-control'
                                }))
    
    username = forms.CharField(max_length=100,
                               required=True,
                               widget=forms.TextInput(attrs={
                                   'class': 'form-control',
                                }))
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username']    



class UpdateProfileForm(forms.ModelForm):
    """This form prepares user's profile pic update form.

    """
    avatar = forms.ImageField(widget= forms.FileInput(attrs={
                                'class': 'form-control-file'
                                }))
    class Meta:
        model = Profile
        fields = ['avatar']
    