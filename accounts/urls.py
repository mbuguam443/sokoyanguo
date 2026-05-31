from django.urls import path, reverse_lazy
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/change-password/', PasswordChangeView.as_view(
        template_name='accounts/change_password.html',
        success_url=reverse_lazy('accounts:password_change_done'),
    ), name='change_password'),
    path('profile/change-password/done/', PasswordChangeDoneView.as_view(
        template_name='accounts/change_password_done.html',
    ), name='password_change_done'),
]
