from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import Notification, NotificationStatus

@login_required
def notifications_dropdown(request):
    profile = getattr(request.user, "userprofile", None)
    if not profile:
        return redirect("unauthorized")

    # Get notifications for this user via NotificationStatus
    notifications = Notification.objects.filter(
        notificationstatus__user=profile,
        archived=False,
        notificationstatus__cleared=False
    ).distinct().order_by('-created_at')

    unread_count = NotificationStatus.objects.filter(
        user=profile,
        is_read=False,
        cleared=False
    ).count()

    return render(request, "partials/_notifications.html", {
        "notifications": notifications,
        "unread_count": unread_count
    })


@login_required
@require_POST
def mark_notifications_read(request):
    profile = getattr(request.user, "userprofile", None)
    if profile:
        NotificationStatus.objects.filter(
            user=profile,
            is_read=False
        ).update(is_read=True)
    return JsonResponse({"status": "ok"})


@login_required
@require_POST
def clear_notifications(request):
    profile = getattr(request.user, "userprofile", None)
    if profile:
        NotificationStatus.objects.filter(
            user=profile
        ).update(cleared=True)  # archive instead of delete
    return JsonResponse({"status": "cleared"})
