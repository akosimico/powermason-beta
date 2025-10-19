from django.conf import settings
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from authentication.models import CustomUser, UserProfile

# Import allauth signal
from allauth.account.signals import email_confirmation_sent
from django.contrib.auth.signals import user_logged_in


@receiver(post_migrate)
def create_superuser(sender, **kwargs):
    """
    Automatically create a default superuser if none exists.
    Runs after migrations.
    """
    if not CustomUser.objects.filter(is_superuser=True).exists():
        email = "jhaynoelbarnedo@gmail.com"
        password = "admin123"

        user = CustomUser.objects.create_superuser(
            email=email,
            password=password,
            first_name="Admin",  # Updated to use first_name instead of full_name
            last_name="User"     # Added last_name
        )

        UserProfile.objects.create(
            user=user,
            role="OM"  # or "VO", "PM", etc.
        )
        print(f"✅ Superuser created: {email} / {password}")


@receiver(email_confirmation_sent)
def log_confirmation_sent(request, confirmation, signup, **kwargs):
    """
    Fires when a confirmation email is sent by django-allauth.
    """
    email_address = confirmation.email_address
    user = email_address.user
    
    # Store email in session for resend functionality
    if request and hasattr(request, 'session'):
        request.session['unverified_email'] = user.email
    
    print(f"📩 Confirmation email sent to {user.email}")
    
    # Optional: You can also log this to a file or database
    # import logging
    # logger = logging.getLogger(__name__)
    # logger.info(f"Verification email sent to {user.email}")


# Optional: Signal to clear session when email is verified
from allauth.account.signals import email_confirmed

@receiver(email_confirmed)
def clear_verification_session(request, email_address, **kwargs):
    """
    Clear the unverified_email from session when email is confirmed
    """
    if request and hasattr(request, 'session'):
        request.session.pop('unverified_email', None)
    
    print(f"✅ Email confirmed for {email_address.email}")


# Optional: Signal to handle user signup completion
from allauth.account.signals import user_signed_up

@receiver(user_signed_up)
def handle_user_signup(request, user, **kwargs):
    """
    Handle additional actions when user signs up
    """
    print(f"👤 New user signed up: {user.email}")
    
@receiver(user_logged_in)
def show_welcome_popup_on_login(sender, request, user, **kwargs):
    """
    Show welcome popup every time user logs in
    """
    request.session['show_welcome_popup'] = True
    print(f"🎉 Setting welcome popup for login: {user.email}")