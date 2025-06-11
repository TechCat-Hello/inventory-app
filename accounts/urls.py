from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import custom_login_view
from inventory import views as inventory_views


urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('login/', views.custom_login_view, name='login'),
    path('admin_dashboard/', inventory_views.admin_dashboard_view, name='admin_dashboard'),
    path('user_dashboard/', inventory_views.user_dashboard_view, name='user_dashboard'),
]
