# manage_client/urls.py - CONSOLIDATED VERSION
from django.urls import path
from . import views

app_name = 'manage_client'

urlpatterns = [
    # ===== CLIENT MANAGEMENT =====
    path('clients/', views.client_management, name='client_management'),
    # Client CRUD operations
    path('clients/add/', views.add_client, name='add_client'),
    path('clients/edit/<int:client_id>/', views.edit_client, name='edit_client'),
    path('clients/delete/<int:client_id>/', views.delete_client, name='delete_client'),
    

    
    # ===== PROJECT TYPE MANAGEMENT (MOVED FROM ADMINISTRATION) =====
    # Project Types Management
    path('project-types/', 
         views.project_types_management, 
         name='project_types_management'),
    
    path('project-types/add/', 
         views.add_project_type, 
         name='add_project_type'),
    
    path('project-types/edit/<int:type_id>/', 
         views.edit_project_type, 
         name='edit_project_type'),
    
    path('project-types/delete/<int:type_id>/', 
         views.delete_project_type, 
         name='delete_project_type'),
    
    path('create-project-type/', views.create_project_type_from_client, name='create_project_type_from_client'),
    
    path('create-project-for-client/<int:client_id>/', views.create_project_for_client, name='create_project_for_client'),
    
    
    # ===== API ENDPOINTS =====
    # Client API endpoints
    path('api/clients/<int:client_id>/', views.get_client, name='get_client'),
    path('api/clients/active/', views.get_active_clients, name='get_active_clients'),
    path('api/clients/search/', views.search_clients, name='search_clients'),
    path('api/client-types/', views.get_client_types, name='get_client_types'),
    path('api/clients/<int:client_id>/projects/', views.get_client_projects, name='get_client_projects'),
    path('api/clients/by-type/', views.clients_by_type, name='clients_by_type'),
    path('api/clients/add/', views.add_client_ajax, name='add_client_ajax'),
    path('api/project-types/', views.get_project_types, name='get_project_types'),
    # Project Type API endpoints
    path('api/project-types/<int:type_id>/', 
         views.get_project_type, 
         name='get_project_type'),
    
    path('api/project-types/active/', 
         views.get_active_project_types, 
         name='get_active_project_types'),
    
    path('api/project-types/available/', 
         views.get_available_project_types, 
         name='get_available_project_types'),
    
    path('api/clients/<int:client_id>/project-types/', views.get_client_project_types, name='get_client_project_types'),
]