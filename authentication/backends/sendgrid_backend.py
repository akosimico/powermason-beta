"""
Custom Django email backend for SendGrid HTTP API.
This bypasses SMTP port blocking on Render by using HTTP API instead.
"""
import requests
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings


class SendGridHTTPBackend(BaseEmailBackend):
    """
    Email backend that uses SendGrid's HTTP API instead of SMTP.
    This works on Render where SMTP ports are blocked.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = getattr(settings, 'SENDGRID_API_KEY', None)
        self.api_url = 'https://api.sendgrid.com/v3/mail/send'

    def send_messages(self, email_messages):
        """
        Send one or more EmailMessage objects and return the number sent.
        """
        if not self.api_key:
            if not self.fail_silently:
                raise ValueError('SENDGRID_API_KEY is not set in environment variables')
            return 0

        num_sent = 0
        for message in email_messages:
            sent = self._send(message)
            if sent:
                num_sent += 1
        return num_sent

    def _send(self, email_message):
        """Send a single email message via SendGrid HTTP API."""
        try:
            # Extract from email
            from_email = email_message.from_email or settings.DEFAULT_FROM_EMAIL

            # Handle "Name <email@example.com>" format
            if '<' in from_email and '>' in from_email:
                from_name = from_email.split('<')[0].strip()
                from_email_address = from_email.split('<')[1].split('>')[0].strip()
            else:
                from_name = None
                from_email_address = from_email

            # Build from object
            from_obj = {'email': from_email_address}
            if from_name:
                from_obj['name'] = from_name

            # Build SendGrid API payload
            payload = {
                'personalizations': [{
                    'to': [{'email': recipient} for recipient in email_message.to],
                }],
                'from': from_obj,
                'subject': email_message.subject,
                'content': [{
                    'type': 'text/plain',
                    'value': email_message.body,
                }],
            }

            # Add CC if present
            if email_message.cc:
                payload['personalizations'][0]['cc'] = [
                    {'email': recipient} for recipient in email_message.cc
                ]

            # Add BCC if present
            if email_message.bcc:
                payload['personalizations'][0]['bcc'] = [
                    {'email': recipient} for recipient in email_message.bcc
                ]

            # Add reply-to if present
            if email_message.reply_to:
                payload['reply_to'] = {
                    'email': email_message.reply_to[0]
                }

            # Send via HTTP API
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            }

            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=10,  # 10 second timeout for HTTP request
            )

            # Check if successful (SendGrid returns 202 Accepted)
            if response.status_code in (200, 202):
                return True
            else:
                error_msg = f'SendGrid API error: {response.status_code}'
                try:
                    error_detail = response.json()
                    error_msg += f' - {error_detail}'
                except:
                    error_msg += f' - {response.text}'

                if not self.fail_silently:
                    raise Exception(error_msg)
                return False

        except requests.exceptions.Timeout:
            if not self.fail_silently:
                raise Exception('SendGrid HTTP API request timed out after 10 seconds')
            return False
        except requests.exceptions.RequestException as e:
            if not self.fail_silently:
                raise Exception(f'SendGrid HTTP API request failed: {str(e)}')
            return False
        except Exception as e:
            if not self.fail_silently:
                raise
            return False
