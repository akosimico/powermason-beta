from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.contrib.auth.views import redirect_to_login
from django.contrib import messages


def verified_email_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.emailaddress_set.filter(verified=True).exists():
                return view_func(request, *args, **kwargs)
            else:
                return redirect('email_verification_required')
        else:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
    return _wrapped_view


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            profile = getattr(request.user, "userprofile", None)
            if profile and profile.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, "You do not have permission to access this page.")
            return redirect("unauthorized")
        return _wrapped_view
    return decorator
