# Toast Notification Helpers
# Centralized toast notification system for the PowerMason project

def set_toast_message(request, message, toast_type="info", duration=5000):
    """
    Set a toast message in the session to be displayed on the next page load.
    
    Args:
        request: Django request object
        message (str): The message to display
        toast_type (str): Type of toast - 'success', 'error', 'warning', 'info'
        duration (int): Duration in milliseconds (default: 5000)
    """
    request.session['show_toast'] = {
        'message': message,
        'type': toast_type,
        'duration': duration
    }

def set_toast_from_messages(request):
    """
    Convert Django messages to toast notifications.
    This should be called after adding Django messages.
    
    Args:
        request: Django request object
    """
    from django.contrib import messages
    
    # Get the most recent message
    message_list = list(messages.get_messages(request))
    if message_list:
        latest_message = message_list[-1]
        
        # Map Django message levels to toast types
        level_mapping = {
            messages.DEBUG: 'info',
            messages.INFO: 'info',
            messages.SUCCESS: 'success',
            messages.WARNING: 'warning',
            messages.ERROR: 'error',
        }
        
        toast_type = level_mapping.get(latest_message.level, 'info')
        set_toast_message(request, str(latest_message), toast_type)

def clear_toast_session(request):
    """
    Clear the toast session data.
    This should be called after displaying the toast.
    
    Args:
        request: Django request object
    """
    if 'show_toast' in request.session:
        del request.session['show_toast']