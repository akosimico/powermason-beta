"""
Email utility functions for sending notifications via SendGrid/SMTP
"""
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def get_site_url():
    """
    Get the site URL for generating links in emails.
    Returns production URL in production, localhost in development.
    """
    return getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000')


def send_email_notification(recipients, subject, html_message, plain_message=None):
    """
    Send an email notification to one or more recipients.

    Args:
        recipients: Email address (string) or list of email addresses
        subject: Email subject line
        html_message: HTML content of the email
        plain_message: Plain text fallback (optional, will strip HTML if not provided)

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Ensure recipients is a list
    if isinstance(recipients, str):
        recipients = [recipients]

    # Filter out empty/None recipients
    recipients = [r for r in recipients if r]

    if not recipients:
        logger.warning("No valid recipients for email notification")
        return False

    # If no plain message provided, create a basic one
    if plain_message is None:
        plain_message = f"{subject}\n\nPlease view this email in an HTML-enabled email client."

    try:
        # Send email using Django's send_mail (uses configured backend)
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Email sent successfully to {len(recipients)} recipient(s): {subject}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email: {subject}. Error: {str(e)}")
        # Don't raise exception - we don't want email failures to break the workflow
        return False


def send_schedule_submitted_email(pm_user, schedule, domain):
    """
    Send confirmation email to PM after submitting schedule.
    """
    context = {
        'domain': domain,
        'pm_name': pm_user.userprofile.full_name,
        'project_code': schedule.project.project_id,
        'project_name': schedule.project.project_name,
        'version': schedule.version,
        'schedule_link': f"{domain}/scheduling/schedule/{schedule.id}/detail/",
    }

    html_message = render_to_string('emails/schedule_submitted.html', context)
    plain_message = f"""
Hello {context['pm_name']},

Your schedule for Project {context['project_code']} - {context['project_name']} (Version {context['version']}) has been submitted successfully and is now waiting for approval from the OM/EG team.

You will receive a notification once your schedule has been reviewed.

View your schedule: {context['schedule_link']}

Best regards,
Powermason Team
    """

    return send_email_notification(
        recipients=pm_user.email,
        subject=f"Schedule Submitted Successfully - Project {context['project_code']}",
        html_message=html_message,
        plain_message=plain_message
    )


def send_schedule_pending_approval_email(om_eg_users, schedule, pm_name, domain):
    """
    Send notification email to OM/EG users about pending schedule approval.
    """
    recipients = [user.user.email for user in om_eg_users if user.user.email]

    context = {
        'domain': domain,
        'pm_name': pm_name,
        'project_code': schedule.project.project_id,
        'project_name': schedule.project.project_name,
        'version': schedule.version,
        'review_link': f"{domain}/scheduling/schedule/{schedule.id}/review/",
    }

    html_message = render_to_string('emails/schedule_pending_approval.html', context)
    plain_message = f"""
Hello,

A new project schedule requires your review and approval.

Project: {context['project_code']} - {context['project_name']}
Version: {context['version']}
Submitted by: {context['pm_name']}

Please review the schedule at your earliest convenience.

Review schedule: {context['review_link']}

Best regards,
Powermason Team
    """

    return send_email_notification(
        recipients=recipients,
        subject=f"New Schedule Pending Approval - Project {context['project_code']}",
        html_message=html_message,
        plain_message=plain_message
    )


def send_schedule_approved_email(pm_user, schedule, approver_name, domain):
    """
    Send notification email to PM when schedule is approved.
    """
    context = {
        'domain': domain,
        'pm_name': pm_user.userprofile.full_name,
        'project_code': schedule.project.project_id,
        'project_name': schedule.project.project_name,
        'version': schedule.version,
        'approver_name': approver_name,
        'schedule_link': f"{domain}/scheduling/schedule/{schedule.id}/detail/",
    }

    html_message = render_to_string('emails/schedule_approved.html', context)
    plain_message = f"""
Hello {context['pm_name']},

Great news! Your schedule for Project {context['project_code']} - {context['project_name']} (Version {context['version']}) has been approved by {context['approver_name']}.

You can now proceed with project execution according to the approved schedule.

View your approved schedule: {context['schedule_link']}

Best regards,
Powermason Team
    """

    return send_email_notification(
        recipients=pm_user.email,
        subject=f"Schedule Approved - Project {context['project_code']}",
        html_message=html_message,
        plain_message=plain_message
    )


def send_schedule_rejected_email(pm_user, schedule, rejector_name, rejection_reason, domain):
    """
    Send notification email to PM when schedule is rejected.
    """
    context = {
        'domain': domain,
        'pm_name': pm_user.userprofile.full_name,
        'project_code': schedule.project.project_id,
        'project_name': schedule.project.project_name,
        'version': schedule.version,
        'rejector_name': rejector_name,
        'rejection_reason': rejection_reason or "No specific reason provided",
        'schedule_link': f"{domain}/scheduling/schedule/{schedule.id}/detail/",
    }

    html_message = render_to_string('emails/schedule_rejected.html', context)
    plain_message = f"""
Hello {context['pm_name']},

Your schedule for Project {context['project_code']} - {context['project_name']} (Version {context['version']}) has been rejected by {context['rejector_name']}.

Reason: {context['rejection_reason']}

Please review the feedback and resubmit your schedule with the necessary corrections.

View schedule: {context['schedule_link']}

Best regards,
Powermason Team
    """

    return send_email_notification(
        recipients=pm_user.email,
        subject=f"Schedule Rejected - Project {context['project_code']}",
        html_message=html_message,
        plain_message=plain_message
    )


def send_progress_report_submitted_email(pm_user, report, domain):
    """
    Send confirmation email to PM after submitting progress report.
    """
    context = {
        'domain': domain,
        'pm_name': pm_user.userprofile.full_name,
        'project_code': report.project.project_id,
        'project_name': report.project.project_name,
        'week_ending': report.week_end_date.strftime('%Y-%m-%d'),
        'report_link': f"{domain}/scheduling/progress/weekly/{report.id}/",
    }

    html_message = render_to_string('emails/progress_report_submitted.html', context)
    plain_message = f"""
Hello {context['pm_name']},

Your weekly progress report for Project {context['project_code']} - {context['project_name']} (Week ending {context['week_ending']}) has been submitted successfully and is now waiting for review from the OM/EG team.

You will receive a notification once your report has been reviewed.

View your report: {context['report_link']}

Best regards,
Powermason Team
    """

    return send_email_notification(
        recipients=pm_user.email,
        subject=f"Progress Report Submitted - {context['project_name']}",
        html_message=html_message,
        plain_message=plain_message
    )


def send_progress_report_pending_email(om_eg_users, report, pm_name, domain):
    """
    Send notification email to OM/EG users about pending progress report review.
    """
    recipients = [user.user.email for user in om_eg_users if user.user.email]

    context = {
        'domain': domain,
        'pm_name': pm_name,
        'project_code': report.project.project_id,
        'project_name': report.project.project_name,
        'week_ending': report.week_end_date.strftime('%Y-%m-%d'),
        'review_link': f"{domain}/scheduling/progress/weekly/{report.id}/",
    }

    html_message = render_to_string('emails/progress_report_pending.html', context)
    plain_message = f"""
Hello,

A new weekly progress report requires your review.

Project: {context['project_code']} - {context['project_name']}
Week Ending: {context['week_ending']}
Submitted by: {context['pm_name']}

Please review the report at your earliest convenience.

Review report: {context['review_link']}

Best regards,
Powermason Team
    """

    return send_email_notification(
        recipients=recipients,
        subject=f"New Progress Report - {context['project_name']} ({context['project_code']})",
        html_message=html_message,
        plain_message=plain_message
    )


def send_progress_report_approved_email(pm_user, report, approver_name, domain):
    """
    Send notification email to PM when progress report is approved.
    """
    context = {
        'domain': domain,
        'pm_name': pm_user.userprofile.full_name,
        'project_code': report.project.project_id,
        'project_name': report.project.project_name,
        'week_ending': report.week_end_date.strftime('%Y-%m-%d'),
        'approver_name': approver_name,
        'report_link': f"{domain}/scheduling/progress/weekly/{report.id}/",
    }

    html_message = render_to_string('emails/progress_report_approved.html', context)
    plain_message = f"""
Hello {context['pm_name']},

Your weekly progress report for Project {context['project_code']} - {context['project_name']} (Week ending {context['week_ending']}) has been approved by {context['approver_name']}.

View your approved report: {context['report_link']}

Best regards,
Powermason Team
    """

    return send_email_notification(
        recipients=pm_user.email,
        subject=f"Progress Report Approved - {context['project_name']}",
        html_message=html_message,
        plain_message=plain_message
    )


def send_progress_report_rejected_email(pm_user, report, rejector_name, rejection_reason, domain):
    """
    Send notification email to PM when progress report is rejected.
    """
    context = {
        'domain': domain,
        'pm_name': pm_user.userprofile.full_name,
        'project_code': report.project.project_id,
        'project_name': report.project.project_name,
        'week_ending': report.week_end_date.strftime('%Y-%m-%d'),
        'rejector_name': rejector_name,
        'rejection_reason': rejection_reason or "No specific reason provided",
        'report_link': f"{domain}/scheduling/progress/weekly/{report.id}/",
    }

    html_message = render_to_string('emails/progress_report_rejected.html', context)
    plain_message = f"""
Hello {context['pm_name']},

Your weekly progress report for Project {context['project_code']} - {context['project_name']} (Week ending {context['week_ending']}) has been rejected by {context['rejector_name']}.

Reason: {context['rejection_reason']}

Please review the feedback and resubmit your report with the necessary corrections.

View report: {context['report_link']}

Best regards,
Powermason Team
    """

    return send_email_notification(
        recipients=pm_user.email,
        subject=f"Progress Report Rejected - {context['project_name']}",
        html_message=html_message,
        plain_message=plain_message
    )
