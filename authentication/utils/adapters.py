from django.conf import settings
from django.contrib.sites.models import Site
from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse
from allauth.utils import build_absolute_uri
from django.contrib import messages

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_email_confirmation_url(self, request, emailconfirmation):
        """
        Constructs the email confirmation (activation) URL.
        """
        url = reverse("account_confirm_email", args=[emailconfirmation.key])
        ret = build_absolute_uri(request, url, protocol=getattr(settings, 'ACCOUNT_DEFAULT_HTTP_PROTOCOL', 'http'))
        return ret

    def confirm_email(self, request, email_address):
        """
        Called after email is confirmed
        """
        print("🔍 CONFIRM_EMAIL DEBUG:")
        print(f"📧 Request path: {request.path}")
        print(f"👤 User: {email_address.user}")
        print(f"✅ Email verified: {email_address.verified}")
    
        # Call the parent method first
        result = super().confirm_email(request, email_address)
        print("✅ Super confirm_email completed")
        
        # DON'T add messages here - they get lost in redirect
        return result

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        """
        Custom email sending with better context
        """
        print("🚀 CUSTOM ADAPTER IS BEING USED!")
        print(f"📝 Signup: {signup}")
        print(f"📧 EmailConfirmation type: {type(emailconfirmation)}")
        print(f"🔑 Key: {emailconfirmation.key}")
        print(f"📬 Email address: {emailconfirmation.email_address}")
        
        current_site = Site.objects.get_current()
        activate_url = self.get_email_confirmation_url(request, emailconfirmation)
        
        print(f"🔗 Generated URL: {activate_url}")
        print(f"📧 Using site: {current_site.name}")
        
        ctx = {
            "user": emailconfirmation.email_address.user,
            "activate_url": activate_url,
            "current_site": current_site,
            "key": emailconfirmation.key,
            "expiration_days": settings.ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS,
        }
        
        email_template = "account/email/email_confirmation"
        self.send_mail(email_template, emailconfirmation.email_address.email, ctx)

    def get_from_email(self):
        """
        This is a hook that can be overridden to provide a custom "from" address
        """
        return getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@powermason.com')