from django.urls import path
from .views import progress_monitoring
from . import views

urlpatterns = [
    # Session-based progress monitoring
    path("", views.progress_monitoring, name="progress_monitoring"),
]
