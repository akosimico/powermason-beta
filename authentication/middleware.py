from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


class LimitMessagesMiddleware:
    """Middleware to limit the number of messages stored"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Limit messages to the last 3
        storage = messages.get_messages(request)
        message_list = list(storage)

        if len(message_list) > 3:
            # Clear all messages
            storage.used = False
            # Re-add only the last 3
            for message in message_list[-3:]:
                messages.add_message(request, message.level, message.message, message.tags)

        return response


class ForcePasswordChangeMiddleware:
    """Middleware to enforce password change for users with force_password_change flag"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if user is authenticated and has a user profile
        if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
            user_profile = request.user.userprofile

            # Check if password change is required
            if user_profile.force_password_change:
                # Exempt URLs that should be accessible
                exempt_urls = [
                    reverse('account_logout'),
                    reverse('account_change_password'),
                    '/accounts/password/change/',  # Alternative path
                    '/static/',  # Allow static files
                    '/media/',   # Allow media files
                ]

                # Check if current path is in exempt URLs
                current_path = request.path
                is_exempt = any(current_path.startswith(url) for url in exempt_urls)

                if not is_exempt:
                    # Add a warning message
                    messages.warning(
                        request,
                        'You must change your password before continuing. '
                        'This is required for security purposes.'
                    )
                    # Redirect to password change page
                    return redirect('account_change_password')

        response = self.get_response(request)
        return response


# TokenGenerationMiddleware removed as tokens are no longer used