from django.urls import path, reverse_lazy
from accounts import views
from django.contrib.auth import views as auth_views
from .views import CustomPasswordResetConfirmView, CustomPasswordResetView

app_name = 'accounts'

urlpatterns = [
    # Registration and Activation
    path('register/', views.register, name='register'),
    path('activate/<slug:uidb64>/<slug:token>/', views.account_activate, name='activate'),

    # Login and Logout
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_user, name='logout'),

    # Password Reset URLs
    path('reset_password/',
         CustomPasswordResetView.as_view(
             template_name='account/password_reset_form.html',
             email_template_name='account/password_reset_email.html',
             success_url=reverse_lazy('accounts:password_reset_done')
         ),
         name='password_reset'),

    path('reset_password_sent/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='account/password_reset_done.html'
         ),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         CustomPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),

    path('reset_password_complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='account/password_reset_complete.html'
         ),
         name='password_reset_complete'),

    # Password Change URLs
    path('password_change/',
         auth_views.PasswordChangeView.as_view(
             template_name='account/password_change_form.html',
             success_url=reverse_lazy('accounts:password_change_done')
         ),
         name='password_change_view'),

    path('password_change_done/',
         auth_views.PasswordChangeDoneView.as_view(
             template_name='account/password_change_done.html'
         ),
         name='password_change_done'),
]
