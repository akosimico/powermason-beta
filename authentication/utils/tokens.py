from authentication.models import UserProfile
from django.contrib import messages


def get_user_profile(request):
    """
    Get the UserProfile for the authenticated user from session.
    Returns the UserProfile if valid, else returns None and adds an error message.
    """
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to access this page.")
        return None

    try:
        profile = UserProfile.objects.get(user=request.user)
        return profile
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found. Please contact an administrator.")
        return None


def verify_user_profile(request, expected_role=None):
    """
    Verifies the user's profile and returns it if valid.
    Optionally validates the expected role.
    """
    profile = get_user_profile(request)
    if not profile:
        return None

    # Validate expected role if provided
    if expected_role and profile.role != expected_role:
        messages.error(request, f"Access denied. This page requires {expected_role} role.")
        return None

    return profile
