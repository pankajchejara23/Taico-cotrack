from django.urls import path
from django.contrib.auth import views as auth_views
from .views import home, RegisterView, CustomLoginView, ResetPasswordView, ChangePasswordView

urlpatterns = [
    path('', home, name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/login.html'), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('password-reset/', ResetPasswordView.as_view(), name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name = 'registration/password_reset_confirm.html'), 
             name='password_reset_confirm'),

    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'),
         name='password_reset_complete'),

    path('password-change/', ChangePasswordView.as_view(), name='password_change'),
    
]