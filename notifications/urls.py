from django.urls import path
from . import views

urlpatterns = [
    path('dropdown/', views.notifications_dropdown, name='notifications_dropdown'),
    path('mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('clear/', views.clear_notifications, name='clear_notifications'),
]
