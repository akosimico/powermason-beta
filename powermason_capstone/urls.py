from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from allauth.account.views import ConfirmEmailView
from xero import views as xero_views

urlpatterns = [
    path('accounts/confirm-email/<str:key>/', ConfirmEmailView.as_view(), name='account_confirm_email'),
    path('admin/', admin.site.urls),
    path('', include('authentication.urls')),
    path('accounts/', include('allauth.urls')),
    path('projects/', include('project_profiling.urls')),
    path("scheduling/", include("scheduling.urls")),
    path('progress-monitoring/', include("progress_monitoring.urls")),
    path("notifications/", include("notifications.urls")),
    path('manage-client/', include("manage_client.urls", namespace='manage_client')),
    path('employees/', include('employees.urls')),
    path('materials/', include('materials_equipment.urls')),


    path('xero/', include('xero.urls')),
    path('xero/connect/', xero_views.xero_connect, name='xero_connect'),
    path('accounts/xero/login/callback/', xero_views.xero_callback, name='xero_callback'),
    path('xero/test/', xero_views.test_xero_api, name='test_xero_api'),
    path('xero/dashboard/', xero_views.xero_dashboard, name='xero_dashboard'),
    path('xero/switch-org/', xero_views.switch_xero_organization, name='switch_xero_org'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)