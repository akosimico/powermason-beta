from django.contrib import messages

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


# TokenGenerationMiddleware removed as tokens are no longer used