from django.urls import path
from . import views
from inventory import views

urlpatterns = [
    path('admin_dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('user_dashboard/', views.user_dashboard_view, name='user_dashboard'),
    path('redirect/', views.redirect_after_login, name='redirect_after_login'),
    path('items/', views.item_list, name='item_list'),
    path('items/<int:pk>/', views.item_detail, name='item_detail'),
    path('items/create/', views.item_create, name='item_create'),
    path('items/<int:pk>/edit/', views.item_update, name='item_update'),
    path('items/<int:pk>/delete/', views.item_delete, name='item_delete'),
    path('items/<int:pk>/edit/', views.edit_item, name='edit_item'),
    path('items/<int:pk>/delete/', views.InventoryItemDeleteView.as_view(), name='item_delete'),
]
