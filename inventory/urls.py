from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('admin_dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('user_dashboard/', views.user_dashboard_view, name='user_dashboard'),
    path('redirect/', views.redirect_after_login, name='redirect_after_login'),
    path('items/', views.item_list, name='item_list'),
    path('items/<int:pk>/', views.item_detail, name='item_detail'),
    path('items/create/', views.item_create, name='item_create'),
    path('items/<int:pk>/edit/', views.item_update, name='edit_item'),
    path('items/<int:pk>/delete/', views.item_delete, name='item_delete'),
    path('rentals/', views.rental_list, name='rental_list'),
    path('rental/create/<int:item_id>/', views.rental_create, name='rental_create'),
    path('return_item/<int:rental_id>/', views.return_item, name='return_item'),
    path('admin_rentals/', views.all_rental_history_view, name='all_rental_history'),
    path('all_rental_history/', views.all_rental_history_view, name='all_rental_history'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('export/csv/', views.export_rentals_csv, name='export_rentals_csv'),
    path('export/excel/', views.export_rentals_excel, name='export_rentals_excel'),
    path('export/pdf/', views.export_rentals_pdf, name='export_rentals_pdf'),
    path('export_all_rentals/csv/', views.export_all_rentals_csv, name='export_all_rentals_csv'),
    path('export_all_rentals/excel/', views.export_all_rentals_excel, name='export_all_rentals_excel'),
    path('export_all_rentals/pdf/', views.export_all_rentals_pdf, name='export_all_rentals_pdf'),
    path('', views.home, name='home'),
]
