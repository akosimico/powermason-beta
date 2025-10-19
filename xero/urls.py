from django.urls import path
from . import views
from manage_client import views as client_views
from xero.xero_sync import SyncClientToXeroView
urlpatterns = [
    path('xero/sync-client/<int:client_id>/', client_views.sync_client_manual, name='sync_single_client'),
    path('api/clients/<int:client_id>/sync-to-xero/', SyncClientToXeroView.as_view(), name='sync_client_to_xero'),
]
