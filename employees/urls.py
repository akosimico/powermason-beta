# urls.py (in your employees app)
from django.urls import path
from . import views

app_name = 'employee'

urlpatterns = [
    # List and Dashboard
    path('', views.EmployeeListView.as_view(), name='list'),
    path('dashboard/', views.employee_dashboard, name='dashboard'),
    
    # CRUD Operations
    path('create/', views.EmployeeCreateView.as_view(), name='create'),
    path('<int:pk>/', views.EmployeeDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.EmployeeUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.EmployeeDeleteView.as_view(), name='delete'),
    
    # Employee Management Actions
    path('<int:pk>/manage-user-profile/', views.manage_user_profile, name='manage_user_profile'),
    path('<int:pk>/extend-contract/', views.extend_contract, name='extend_contract'),
    path('<int:pk>/toggle-status/', views.toggle_employee_status, name='toggle_status'),
    path('<int:pk>/assign-to-project/', views.assign_to_project, name='assign_to_project'),
    
    # Utility Functions
    path('export-csv/', views.export_employees_csv, name='export_csv'),
    path('send-notifications/', views.send_contract_notifications, name='send_notifications'),
    
    # API Endpoints
    path('api/search/', views.employee_search_api, name='search_api'),
    path('api/projects/', views.get_available_projects_api, name='projects_api'),
]