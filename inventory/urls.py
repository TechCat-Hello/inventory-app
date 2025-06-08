from django.urls import path
from . import views
from inventory import views

urlpatterns = [
    path('admin_dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('user_dashboard/', views.user_dashboard_view, name='user_dashboard'),
    path('redirect/', views.redirect_after_login, name='redirect_after_login'),
]
