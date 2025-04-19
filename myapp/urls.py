from django.urls import path
from . import views

urlpatterns = [
    #Landing Page
        #path('', views.landing_page, name='landing'),

    #Data Processing
    path('upload/', views.upload_file, name='upload'),
    path('result/', views.result_view, name='result'),
    path('data/', views.data_overview, name='data_overview'),
    path('data/edit/<int:id>/', views.edit_data, name='edit_data'),
    path('data/delete/<int:id>/', views.delete_data, name='delete_data'),

    #Admin / User
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('admin-dashboard', views.admin_dashboard, name='admin_dashboard'),#Admin login
    path('user-dashboard', views.user_dashboard, name='user_dashboard'),# User login

    #Forbidden
    path('forbidden/', views.forbidden_access, name='forbidden_access'),

    #Manage Users
    path('manage-users/', views.manage_users_view, name='manage_users'),
    path('create-user/', views.create_user_view, name='create_user'),
    path('edit-user/<int:user_id>/', views.edit_user_view, name='edit_user'),
    path('delete-user/<int:user_id>/', views.delete_user_view, name='delete_user'),
    path('change-password/', views.user_change_password, name='change_password'),
    path('admin-change-password/', views.admin_change_password, name='admin_change_password'),

]
