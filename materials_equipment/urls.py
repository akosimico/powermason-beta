from django.urls import path
from . import views

app_name = 'materials_equipment'

urlpatterns = [
    # Materials Views
    path('materials/', views.material_list, name='material_list'),
    path('materials/create/', views.material_create, name='material_create'),
    path('materials/<int:pk>/edit/', views.material_edit, name='material_edit'),
    path('materials/<int:pk>/delete/', views.material_delete, name='material_delete'),

    # Equipment Views
    path('equipment/', views.equipment_list, name='equipment_list'),
    path('equipment/create/', views.equipment_create, name='equipment_create'),
    path('equipment/<int:pk>/edit/', views.equipment_edit, name='equipment_edit'),
    path('equipment/<int:pk>/delete/', views.equipment_delete, name='equipment_delete'),

    # Price Monitoring
    path('price-monitoring/', views.price_monitoring_dashboard, name='price_monitoring'),
    path('price-monitoring/create/', views.price_monitoring_create, name='price_monitoring_create'),
    path('price-monitoring/<int:pk>/edit/', views.price_monitoring_edit, name='price_monitoring_edit'),
    path('price-monitoring/<int:pk>/delete/', views.price_monitoring_delete, name='price_monitoring_delete'),

    # API Endpoints
    path('api/materials/', views.api_material_list, name='api_material_list'),
    path('api/materials/<int:pk>/', views.api_material_detail, name='api_material_detail'),
    path('api/equipment/', views.api_equipment_list, name='api_equipment_list'),
    path('api/equipment/<int:pk>/', views.api_equipment_detail, name='api_equipment_detail'),
    path('api/manpower/', views.api_manpower_list, name='api_manpower_list'),
    path('api/price-comparison/', views.api_price_comparison, name='api_price_comparison'),
    path('api/price-monitoring/', views.api_price_monitoring_list, name='api_price_monitoring_list'),
]
