# employees/models.py
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from authentication.models import UserProfile
from datetime import date, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)


# Custom QuerySet and Manager
class EmployeeQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status='active')

    def expiring_soon(self, days=30):
        """Get employees with contracts expiring within specified days"""
        future_date = date.today() + timedelta(days=days)
        return self.filter(
            contract_end_date__lte=future_date,
            contract_end_date__gt=date.today(),
            status='active',
        )

    def expired(self):
        """Get employees with expired contracts"""
        return self.filter(
            contract_end_date__lt=date.today(),
            status='active',
        )

    def project_managers(self):
        return self.filter(role='PM')


class EmployeeManager(models.Manager):
    def get_queryset(self):
        return EmployeeQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def expiring_soon(self, days=30):
        return self.get_queryset().expiring_soon(days)

    def expired(self):
        return self.get_queryset().expired()

    def project_managers(self):
        return self.get_queryset().project_managers()


class Employee(models.Model):
    """
    Employee model for construction project roles
    """

    EMPLOYEE_ROLE_CHOICES = [
        ("PM", "Project Manager"),
        ("PIC", "Project In Charge"),
        ("SO", "Safety Officer"),
        ("QA", "Quality Assurance Officer"),
        ("QO", "Quality Officer"),
        ("FM", "Foreman"),
        ("LB", "Labor"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("on_leave", "On Leave"),
        ("terminated", "Terminated"),
    ]

    # Basic Information
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        help_text="Company employee ID",
    )

    # Personal Details
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)


    # Employment Details
    role = models.CharField(max_length=3, choices=EMPLOYEE_ROLE_CHOICES)
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="active",
    )
    hire_date = models.DateField()
    contract_end_date = models.DateField(
        blank=True,
        null=True,
        help_text="Contract expiration date",
    )
    department = models.CharField(max_length=50, blank=True, null=True)

    # Contract tracking
    contract_expiry_notified = models.BooleanField(
        default=False,
        help_text="Has been notified about contract expiry",
    )
    auto_deactivated = models.BooleanField(
        default=False,
        help_text="Was automatically deactivated due to contract expiry",
    )

    # Optional link to UserProfile for employees who have system access
    user_profile = models.ForeignKey(
        'authentication.UserProfile',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='employees',
    )

    # Labor-specific field
    labor_count = models.PositiveIntegerField(
        default=1,
        help_text="For labor roles, this can represent number of workers",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_employees',
    )

    # Custom manager
    objects = EmployeeManager()

    class Meta:
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['employee_id']),
            models.Index(fields=['role', 'status']),
            models.Index(fields=['contract_end_date']),
        ]

    def __str__(self):
        return f"{self.full_name} - {self.get_role_display()}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_active(self):
        return self.status == 'active'

    @property
    def is_contract_expired(self):
        """Check if contract has expired"""
        if self.contract_end_date:
            return date.today() > self.contract_end_date
        return False

    @property
    def days_until_contract_expiry(self):
        """Calculate days until contract expires"""
        if self.contract_end_date:
            delta = self.contract_end_date - date.today()
            return delta.days if delta.days > 0 else 0
        return None

    @property
    def contract_expiring_soon(self):
        """Check if contract is expiring within 30 days"""
        days_left = self.days_until_contract_expiry
        return days_left is not None and 0 < days_left <= 30

    def save(self, *args, **kwargs):
        # Auto-generate employee_id if not provided
        if not self.employee_id:
            self.employee_id = self.generate_employee_id()

        # Handle contract expiration
        if self.is_contract_expired and self.status == 'active':
            self.status = 'inactive'
            self.auto_deactivated = True

        super().save(*args, **kwargs)

    def send_contract_expiry_notification(self):
        """
        Send notification about contract expiry
        Returns True if notification was sent successfully, False otherwise
        """
        try:
            if self.contract_expiry_notified:
                return False  # Already notified

            days_left = self.days_until_contract_expiry
            if days_left is None:
                return False

            from django.core.mail import EmailMultiAlternatives
            from django.conf import settings

            # Determine urgency and status
            is_expired = self.is_contract_expired
            urgency = "URGENT" if (is_expired or days_left <= 7) else "NOTICE"
            status_text = "EXPIRED" if is_expired else "EXPIRING SOON"

            subject = (
                f"[{urgency}] Contract {status_text}: "
                f"{self.full_name} ({self.employee_id})"
            )

            # Plain text message
            plain_message = f"""
EMPLOYEE CONTRACT ALERT

Employee Information:
- Name: {self.full_name}
- Employee ID: {self.employee_id}
- Role: {self.get_role_display()}
- Department: {self.department or 'Not specified'}
- Email: {self.email or 'Not provided'}
- Phone: {self.phone or 'Not provided'}

Contract Details:
- End Date: {self.contract_end_date.strftime('%B %d, %Y')}
- Days Remaining: {days_left}
- Status: {status_text}
- Hire Date: {self.hire_date.strftime('%B %d, %Y')}

REQUIRED ACTION:
{'IMMEDIATE attention required - contract has expired' if is_expired else f'Please review and renew contract within {days_left} days'}

Next Steps:
1. Contact employee to discuss contract renewal
2. Prepare renewal documentation if applicable
3. Update HR records with new contract terms
4. Set new contract end date in the system

Generated: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}

This is an automated notification from PowerMason Employee Management System.
For questions, contact HR at hr@powermason.com
            """

            # Professional HTML email template
            from django.utils import timezone as django_timezone
            import pytz

            # Get Philippines timezone
            ph_tz = pytz.timezone('Asia/Manila')
            current_time_ph = django_timezone.now().astimezone(ph_tz)

            html_message = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contract Notification - PowerMason</title>
    <!--[if mso]>
    <noscript>
        <xml>
            <o:OfficeDocumentSettings>
                <o:PixelsPerInch>96</o:PixelsPerInch>
            </o:OfficeDocumentSettings>
        </xml>
    </noscript>
    <![endif]-->
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.5;
            color: #111827;
            background-color: #f9fafb;
            margin: 0;
            padding: 20px 0;
            -webkit-text-size-adjust: 100%;
            -ms-text-size-adjust: 100%;
        }}

        .email-wrapper {{
            max-width: 650px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }}

        /* Header */
        .header {{
            background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
            padding: 40px 30px;
            text-align: center;
            position: relative;
        }}

        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="50" cy="50" r="0.5" fill="rgba(255,255,255,0.05)"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
            opacity: 0.3;
        }}

        .logo {{
            position: relative;
            z-index: 1;
        }}

        .logo h1 {{
            color: #ffffff;
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
            letter-spacing: -0.025em;
        }}

        .logo p {{
            color: #d1d5db;
            font-size: 16px;
            font-weight: 500;
        }}

        /* Alert Banner */
        .alert-banner {{
            background-color: {'#dc2626' if is_expired else '#ea580c' if days_left <= 7 else '#d97706'};
            color: white;
            padding: 20px 30px;
            text-align: center;
            font-weight: 600;
            font-size: 16px;
            letter-spacing: 0.025em;
        }}

        /* Content */
        .content {{ padding: 40px 30px; }}

        /* Status Badge */
        .status-badge {{
            display: inline-flex;
            align-items: center;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 32px;
            background-color: {'#fef2f2' if is_expired else '#fff7ed' if days_left <= 7 else '#fefbeb'};
            color: {'#dc2626' if is_expired else '#ea580c' if days_left <= 7 else '#d97706'};
            border: 1px solid {'#fecaca' if is_expired else '#fed7aa' if days_left <= 7 else '#fde68a'};
        }}

        /* Employee Card */
        .employee-card {{
            background: #f8fafc;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 32px;
            margin-bottom: 32px;
        }}

        .employee-header {{
            display: flex;
            align-items: center;
            margin-bottom: 24px;
            padding-bottom: 24px;
            border-bottom: 1px solid #e5e7eb;
        }}


        .employee-details h2 {{
            color: #111827;
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 4px;
            line-height: 1.2;
        }}

        .employee-details .employee-meta {{
            color: #6b7280;
            font-size: 15px;
            font-weight: 500;
        }}

        /* Contract Details */
        .contract-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-top: 24px;
        }}

        .detail-item {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
            text-align: center;
        }}

        .detail-label {{
            font-size: 12px;
            color: #6b7280;
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
        }}

        .detail-value {{
            color: #111827;
            font-weight: 700;
            font-size: 16px;
        }}

        /* Days Counter */
        .days-counter {{
            text-align: center;
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 32px;
            margin: 32px 0;
        }}

        .days-number {{
            font-size: 56px;
            font-weight: 800;
            color: {'#dc2626' if is_expired else '#ea580c' if days_left <= 7 else '#d97706'};
            line-height: 1;
            margin-bottom: 8px;
        }}

        .days-text {{
            color: #6b7280;
            font-size: 14px;
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 0.05em;
        }}

        /* Action Section */
        .action-section {{
            background: {'#fef2f2' if is_expired else '#fff7ed'};
            border: 1px solid {'#fecaca' if is_expired else '#fed7aa'};
            border-radius: 12px;
            padding: 32px;
            margin: 32px 0;
        }}

        .action-title {{
            color: {'#dc2626' if is_expired else '#ea580c'};
            font-weight: 700;
            font-size: 18px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
        }}

        .action-title::before {{
            content: "⚠️";
            margin-right: 8px;
            font-size: 20px;
        }}

        .action-list {{
            list-style: none;
            padding: 0;
        }}

        .action-list li {{
            color: #374151;
            margin-bottom: 12px;
            padding-left: 24px;
            position: relative;
            font-size: 15px;
            line-height: 1.5;
        }}

        .action-list li::before {{
            content: "•";
            color: {'#dc2626' if is_expired else '#ea580c'};
            font-weight: bold;
            position: absolute;
            left: 8px;
            font-size: 16px;
        }}

        /* Contact Section */
        .contact-section {{
            background: #f0f9ff;
            border: 1px solid #bfdbfe;
            border-radius: 12px;
            padding: 24px;
            margin: 32px 0;
        }}

        .contact-title {{
            color: #1e40af;
            font-weight: 600;
            font-size: 16px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
        }}

        .contact-title::before {{
            content: "📞";
            margin-right: 8px;
        }}

        .contact-item {{
            color: #374151;
            margin: 8px 0;
            font-size: 14px;
        }}

        .contact-item strong {{
            color: #111827;
            font-weight: 600;
        }}

        /* Footer */
        .footer {{
            background: #f8fafc;
            padding: 30px;
            text-align: center;
            border-top: 1px solid #e5e7eb;
        }}

        .footer-content {{
            color: #6b7280;
            font-size: 13px;
            line-height: 1.6;
        }}

        .footer-brand {{
            color: #111827;
            font-weight: 600;
            margin-bottom: 8px;
        }}

        .footer-timestamp {{
            color: #9ca3af;
            font-size: 12px;
            margin: 12px 0;
        }}

        .footer-legal {{
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid #e5e7eb;
            color: #9ca3af;
            font-size: 11px;
        }}

        /* Mobile Responsive */
        @media only screen and (max-width: 600px) {{
            body {{ padding: 10px 0; }}
            .email-wrapper {{ margin: 0 10px; }}
            .header {{ padding: 30px 20px; }}
            .content {{ padding: 30px 20px; }}
            .employee-card {{ padding: 24px; }}
            .contract-details {{ grid-template-columns: 1fr; }}
            .employee-header {{
                flex-direction: column;
                text-align: center;
            }}
            
            .days-number {{ font-size: 48px; }}
            .action-section {{ padding: 24px; }}
            .footer {{ padding: 24px 20px; }}
        }}
    </style>
</head>
<body>
    <div class="email-wrapper">
        <!-- Header -->
        <div class="header">
            <div class="logo">
                <h1>PowerMason</h1>
                <p>Employee Management System</p>
            </div>
        </div>

        <!-- Alert Banner -->
        <div class="alert-banner">
            {'🚨 CONTRACT EXPIRED' if is_expired else f'⚠️ CONTRACT EXPIRES IN {days_left} DAY{"S" if days_left != 1 else ""}'}
        </div>

        <!-- Content -->
        <div class="content">
            <!-- Status Badge -->
            <div class="status-badge">
                {status_text}
            </div>

            <!-- Employee Card -->
            <div class="employee-card">
                <div class="employee-header">
                    <div class="employee-details">
                        <h2>{self.full_name}</h2>
                        <div class="employee-meta">{self.employee_id} • {self.get_role_display()}</div>
                    </div>
                </div>

                <div class="contract-details">
                    <div class="detail-item">
                        <div class="detail-label">Contract End Date</div>
                        <div class="detail-value">{self.contract_end_date.strftime('%b %d, %Y')}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Department</div>
                        <div class="detail-value">{self.department or 'Not specified'}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Email Address</div>
                        <div class="detail-value">{self.email or 'Not provided'}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Hire Date</div>
                        <div class="detail-value">{self.hire_date.strftime('%b %d, %Y')}</div>
                    </div>
                </div>
            </div>

            <!-- Days Counter -->
            <div class="days-counter">
                <div class="days-number">
                    {'0' if is_expired else days_left}
                </div>
                <div class="days-text">
                    {'Days Overdue' if is_expired else 'Days Remaining'}
                </div>
            </div>


            <!-- Contact Information -->
            <div class="contact-section">
                <div class="contact-title">Need Assistance?</div>
                <div class="contact-item">HR Department: <strong>hr@powermason.com</strong></div>
                <div class="contact-item">Operations Team: <strong>operations@powermason.com</strong></div>
            </div>
        </div>

        <!-- Footer -->
        <div class="footer">
            <div class="footer-content">
                <div class="footer-brand">PowerMason Employee Management System</div>
                <div class="footer-timestamp">Generated on {current_time_ph.strftime('%B %d, %Y at %I:%M %p')} (Philippine Time)</div>
                <div>This is an automated notification. Please do not reply to this email.</div>
                <div class="footer-legal">
                    © 2025 PowerMason Construction. All rights reserved.
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""

            # Replace these with your actual recipient emails
            recipient_list = [
                'hr@powermason.com',
                'operations@powermason.com',
                'powermasonwebsite@gmail.com',
            ]

            if self.email and self.email not in recipient_list:
                recipient_list.append(self.email)

            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_list,
            )
            email.attach_alternative(html_message, "text/html")
            email.send()

            logger.info(
                f"Contract notification sent successfully for "
                f"{self.full_name} to {recipient_list}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to send contract notification for {self.full_name}: {e}"
            )
            return False

    def generate_employee_id(self):
        """Generate a unique employee ID"""
        prefix = self.role
        last_employee = Employee.objects.filter(
            employee_id__startswith=prefix
        ).order_by('employee_id').last()

        if last_employee and last_employee.employee_id:
            try:
                number_part = last_employee.employee_id[len(prefix):]
                last_number = int(number_part)
                new_number = last_number + 1
            except (ValueError, TypeError):
                new_number = 1
        else:
            new_number = 1

        return f"{prefix}{new_number:04d}"  # e.g., PM0001, SO0023

    def activate(self):
        """Activate the employee"""
        self.status = 'active'
        self.auto_deactivated = False
        self.save()

    def deactivate(self, reason='manual'):
        """Deactivate the employee"""
        self.status = 'inactive'
        if reason == 'contract_expired':
            self.auto_deactivated = True
        self.save()

    def extend_contract(self, new_end_date):
        """Extend the employee's contract"""
        self.contract_end_date = new_end_date
        self.contract_expiry_notified = False
        if self.auto_deactivated:
            self.status = 'active'
            self.auto_deactivated = False
        self.save()

    def reset_notification_status(self):
        """Reset notification status (useful for testing)"""
        self.contract_expiry_notified = False
        self.save()


class ProjectAssignment(models.Model):
    """
    Many-to-many relationship between employees and projects
    """

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='project_assignments',
    )
    project = models.ForeignKey(
        'project_profiling.ProjectProfile',
        on_delete=models.CASCADE,
        related_name='employee_assignments',
    )
    assigned_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_lead = models.BooleanField(
        default=False,
        help_text="Is this employee the lead for this role on this project?",
    )

    # Additional fields
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ['employee', 'project']
        ordering = ['-assigned_date']

    def __str__(self):
        return f"{self.employee.full_name} on {self.project}"

    @property
    def is_active(self):
        """Check if assignment is currently active"""
        today = date.today()
        if self.end_date:
            return self.assigned_date <= today <= self.end_date
        return self.assigned_date <= today

    @property
    def duration_days(self):
        """Calculate assignment duration in days"""
        if self.end_date:
            return (self.end_date - self.assigned_date).days
        return (date.today() - self.assigned_date).days
