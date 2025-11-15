"""
Weekly Progress Report Views
Handles submission and management of weekly BOQ-based progress reports
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO
import json
import os
import pytz

from authentication.utils.decorators import role_required
from authentication.utils.toast_helpers import set_toast_message
from project_profiling.models import ProjectProfile, BOQItemProgress
from project_profiling.utils.progress_template_generator import generate_progress_template
from project_profiling.utils.progress_excel_exporter import (
    export_weekly_report_to_excel,
    export_multiple_reports_to_excel
)
from project_profiling.utils.progress_template_excel import generate_blank_template
from project_profiling.utils.progress_template_excel_v2 import generate_blank_template_v2
from project_profiling.utils.progress_excel_reader import read_progress_excel
from .models import WeeklyProgressReport, ProjectTask
from .forms import WeeklyProgressReportForm, ProgressReportRejectionForm

import logging

try:
    from weasyprint import HTML
    WEASY_PRINT_AVAILABLE = True
except ImportError:
    WEASY_PRINT_AVAILABLE = False

logger = logging.getLogger(__name__)


@login_required
@role_required('PM')
def submit_weekly_progress(request, project_id):
    """
    PM submits weekly progress report.
    Generates template with pre-filled BOQ items and allows entry of cumulative progress.
    """
    project = get_object_or_404(ProjectProfile, id=project_id)

    # Check if project has approved schedule
    if not project.tasks.exists():
        messages.error(request, "This project doesn't have an approved schedule yet. Please upload and get schedule approved first.")
        return redirect('project_view', project_source=project.project_source, pk=project.id)

    # Check if project is completed
    if project.status == 'CP':
        messages.error(request, "Cannot submit new progress reports - Project has been marked as Completed.")
        return redirect('list_weekly_reports', project_id=project.id)

    # Handle form submission
    if request.method == 'POST':
        form = WeeklyProgressReportForm(request.POST)

        if form.is_valid():
            week_start = form.cleaned_data['week_start_date']
            week_end = form.cleaned_data['week_end_date']
            remarks = form.cleaned_data.get('remarks', '')

            # Check if report already exists for this week
            existing_report = WeeklyProgressReport.objects.filter(
                project=project,
                week_start_date=week_start
            ).first()

            if existing_report:
                # Allow resubmission only if the previous report was rejected
                if existing_report.status == 'R':
                    # Delete the rejected report to allow new submission
                    existing_report.delete()
                    logger.info(f"Deleted rejected report {existing_report.id} to allow resubmission")
                else:
                    messages.error(
                        request,
                        f"A progress report already exists for week {week_start} to {week_end}. "
                        f"Status: {existing_report.get_status_display()}. Cannot submit duplicate report."
                    )
                    return redirect('submit_weekly_progress', project_id=project.id)

            # Generate template with BOQ items
            try:
                template_data = generate_progress_template(project, week_start, week_end)

                # Save to session for next step
                request.session['progress_template'] = template_data
                request.session['progress_remarks'] = remarks

                # Redirect to BOQ items entry page
                return redirect('enter_boq_progress', project_id=project.id)

            except Exception as e:
                logger.error(f"Error generating progress template: {str(e)}")
                messages.error(request, f"Error generating progress report template: {str(e)}")

    else:
        # Pre-fill with current week
        today = timezone.now().date()
        # Get Monday of current week
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        form = WeeklyProgressReportForm(initial={
            'week_start_date': week_start,
            'week_end_date': week_end
        })

    # Get recent reports for this project
    recent_reports = WeeklyProgressReport.objects.filter(
        project=project
    ).order_by('-week_start_date')[:3]

    context = {
        'project': project,
        'form': form,
        'recent_reports': recent_reports,
    }

    return render(request, 'scheduling/weekly_progress/submit_report.html', context)


@login_required
@role_required('PM')
def enter_boq_progress(request, project_id):
    """
    PM enters cumulative progress for each BOQ item.
    Uses template generated in previous step.
    """
    project = get_object_or_404(ProjectProfile, id=project_id)

    # Get template from session
    template_data = request.session.get('progress_template')
    remarks = request.session.get('progress_remarks', '')

    if not template_data:
        messages.error(request, "No progress template found. Please start from the beginning.")
        return redirect('submit_weekly_progress', project_id=project.id)

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Create weekly report
                report = WeeklyProgressReport.objects.create(
                    project=project,
                    week_start_date=datetime.fromisoformat(template_data['week_start_date']).date(),
                    week_end_date=datetime.fromisoformat(template_data['week_end_date']).date(),
                    remarks=remarks,
                    submitted_by=request.user.userprofile,
                    status='P'  # Pending
                )

                # Process BOQ item progress entries
                boq_items_saved = 0

                for division in template_data['divisions']:
                    for task_data in division['tasks']:
                        task = ProjectTask.objects.get(id=task_data['task_id'])

                        for boq_item in task_data['boq_items']:
                            boq_code = boq_item['code']

                            # Get submitted values from form
                            cumulative_percent = request.POST.get(f'cumulative_percent_{boq_code}')
                            cumulative_amount = request.POST.get(f'cumulative_amount_{boq_code}')
                            item_remarks = request.POST.get(f'remarks_{boq_code}', '')
                            decrease_reason = request.POST.get(f'decrease_reason_{boq_code}', '')

                            if cumulative_percent:  # Only save if value provided
                                cumulative_percent = Decimal(cumulative_percent)

                                # Auto-calculate amount if not provided
                                if not cumulative_amount or cumulative_amount == '':
                                    approved_amount = Decimal(str(boq_item['approved_amount']))
                                    cumulative_amount = (cumulative_percent / 100) * approved_amount
                                else:
                                    cumulative_amount = Decimal(cumulative_amount)

                                # Create BOQ item progress record
                                BOQItemProgress.objects.create(
                                    project=project,
                                    weekly_report=report,
                                    boq_item_code=boq_code,
                                    description=boq_item['description'],
                                    division=division['name'],
                                    task_group=task_data['task_name'],
                                    project_task=task,
                                    approved_contract_amount=Decimal(str(boq_item['approved_amount'])),
                                    quantity=Decimal(str(boq_item.get('quantity', 0))),
                                    unit_of_measurement=boq_item.get('uom', ''),
                                    cumulative_percent=cumulative_percent,
                                    cumulative_amount=cumulative_amount,
                                    previous_cumulative_percent=Decimal(str(boq_item['previous_cumulative_percent'])),
                                    previous_cumulative_amount=Decimal(str(boq_item['previous_cumulative_amount'])),
                                    scheduled_start_date=datetime.fromisoformat(boq_item['scheduled_start_date']).date(),
                                    scheduled_end_date=datetime.fromisoformat(boq_item['scheduled_end_date']).date(),
                                    status='P',  # Pending
                                    reported_by=request.user.userprofile,
                                    report_date=report.week_end_date,
                                    remarks=item_remarks,
                                    decrease_reason=decrease_reason
                                )

                                boq_items_saved += 1

                if boq_items_saved == 0:
                    raise ValueError("No BOQ items were filled in. Please enter progress for at least one item.")

                # Calculate report totals
                report.calculate_totals()

                # Validate against schedule
                warnings = report.validate_against_schedule()

                # Clear session
                if 'progress_template' in request.session:
                    del request.session['progress_template']
                if 'progress_remarks' in request.session:
                    del request.session['progress_remarks']

                messages.success(
                    request,
                    f"Weekly progress report submitted successfully! {boq_items_saved} BOQ items reported. "
                    f"Report is now pending approval by Operations Manager."
                )

                if warnings:
                    messages.warning(
                        request,
                        f"Note: {len(warnings)} schedule validation warnings were detected. "
                        "These will be reviewed during approval."
                    )

                return redirect('view_weekly_report', report_id=report.id)

        except Exception as e:
            logger.error(f"Error saving weekly progress report: {str(e)}")
            messages.error(request, f"Error saving progress report: {str(e)}")

    context = {
        'project': project,
        'template_data': template_data,
        'remarks': remarks,
    }

    return render(request, 'scheduling/weekly_progress/enter_progress.html', context)


@login_required
def view_weekly_report(request, report_id):
    """View details of a weekly progress report"""
    report = get_object_or_404(WeeklyProgressReport, id=report_id)

    # Get all BOQ items for this report
    boq_items = BOQItemProgress.objects.filter(
        weekly_report=report
    ).select_related('project_task').order_by('boq_item_code')

    # Group by division
    divisions = {}
    for item in boq_items:
        if item.division not in divisions:
            divisions[item.division] = []
        divisions[item.division].append(item)

    # Check if user came from project view
    from_project_view = request.GET.get('from_project', 'false') == 'true'

    context = {
        'report': report,
        'project': report.project,
        'divisions': divisions,
        'can_approve': request.user.userprofile.role in ['OM', 'EG'] and report.status == 'P',
        'can_edit': request.user.userprofile.role == 'PM' and report.status == 'R',  # Can edit if rejected
        'from_project_view': from_project_view,
    }

    return render(request, 'scheduling/weekly_progress/view_report.html', context)


@login_required
def list_weekly_reports(request, project_id):
    """List all weekly progress reports for a project"""
    project = get_object_or_404(ProjectProfile, id=project_id)

    # Filter by status if provided
    status_filter = request.GET.get('status', 'all')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search_date = request.GET.get('search_date')

    reports = WeeklyProgressReport.objects.filter(project=project)

    # Apply status filter
    if status_filter != 'all':
        reports = reports.filter(status=status_filter)

    # Apply date range filter - check for overlap with the selected range
    # A report overlaps if: report_start <= range_end AND report_end >= range_start
    if start_date and end_date:
        from datetime import datetime
        from django.db.models import Q
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            reports = reports.filter(
                Q(week_start_date__lte=end) & Q(week_end_date__gte=start)
            )
        except ValueError:
            from authentication.utils.toast_helpers import set_toast_message
            set_toast_message(request, "Invalid date format. Please use YYYY-MM-DD.", "error")

    # Apply specific date search (report contains this date)
    if search_date:
        from datetime import datetime
        try:
            search = datetime.strptime(search_date, '%Y-%m-%d').date()
            reports = reports.filter(
                week_start_date__lte=search,
                week_end_date__gte=search
            )
        except ValueError:
            from authentication.utils.toast_helpers import set_toast_message
            set_toast_message(request, "Invalid date format. Please use YYYY-MM-DD.", "error")

    reports = reports.order_by('-week_start_date')

    context = {
        'project': project,
        'reports': reports,
        'status_filter': status_filter,
        'start_date': start_date,
        'end_date': end_date,
        'search_date': search_date,
    }

    return render(request, 'scheduling/weekly_progress/list_reports.html', context)


@login_required
@role_required('OM', 'EG')
def review_weekly_reports(request):
    """
    OM/EG view to review all pending weekly progress reports.
    Shows reports from all projects awaiting approval.
    """
    # Get all pending reports
    pending_reports = WeeklyProgressReport.objects.filter(
        status='P'
    ).select_related('project', 'submitted_by').order_by('-submitted_at')

    context = {
        'pending_reports': pending_reports,
    }

    return render(request, 'scheduling/weekly_progress/review_reports.html', context)


@login_required
@role_required('OM', 'EG')
def approve_weekly_report(request, report_id):
    """OM/EG approves a weekly progress report"""
    report = get_object_or_404(WeeklyProgressReport, id=report_id)

    if report.status != 'P':
        messages.error(request, "This report has already been reviewed.")
        return redirect('view_weekly_report', report_id=report.id)

    if request.method == 'POST':
        try:
            # Check if there are any pending reports with earlier report numbers
            earlier_pending_reports = WeeklyProgressReport.objects.filter(
                project=report.project,
                status='P',  # Pending
                report_number__lt=report.report_number  # Earlier report numbers
            ).order_by('report_number')

            if earlier_pending_reports.exists():
                # Get the first pending report that needs to be approved
                first_pending = earlier_pending_reports.first()

                set_toast_message(
                    request,
                    f"Cannot approve Report #{report.report_number}. Please approve Report #{first_pending.report_number} "
                    f"(Week: {first_pending.week_start_date.strftime('%b %d')} - {first_pending.week_end_date.strftime('%b %d, %Y')}) first.",
                    "error"
                )

                messages.error(
                    request,
                    f"⚠️ Sequential approval required: Report #{first_pending.report_number} must be approved before Report #{report.report_number}."
                )

                return redirect('view_weekly_report', report_id=report.id)

            # Approve the report
            report.approve(reviewer=request.user.userprofile)

            # Toast message for approval success
            set_toast_message(
                request,
                f"Progress report #{report.report_number} approved successfully! Project progress updated.",
                "success"
            )

            messages.success(
                request,
                f"Progress report for week {report.week_start_date} to {report.week_end_date} approved successfully! "
                "Task and project progress have been updated."
            )

            # Notify PM that their report was approved
            from notifications.models import Notification, NotificationStatus
            notification = Notification.objects.create(
                message=f"Your weekly progress report for {report.project.project_name} was approved (Week: {report.week_start_date.strftime('%b %d')} - {report.week_end_date.strftime('%b %d, %Y')})",
                link=f"/scheduling/progress/weekly/{report.id}/",
                role='PM'
            )
            NotificationStatus.objects.create(
                notification=notification,
                user=report.submitted_by,
                is_read=False
            )

            # Send email notification to PM
            from notifications.email_utils import send_progress_report_approved_email, get_site_url

            domain = get_site_url()
            send_progress_report_approved_email(
                pm_user=report.submitted_by.user,
                report=report,
                approver_name=request.user.userprofile.full_name,
                domain=domain
            )

            # Redirect back to the review weekly reports page
            return redirect('review_weekly_reports')

        except Exception as e:
            logger.error(f"Error approving report: {str(e)}")
            messages.error(request, f"Error approving report: {str(e)}")

    return redirect('view_weekly_report', report_id=report.id)


@login_required
@role_required('OM', 'EG')
def reject_weekly_report(request, report_id):
    """OM/EG rejects a weekly progress report with reason"""
    report = get_object_or_404(WeeklyProgressReport, id=report_id)

    if report.status != 'P':
        messages.error(request, "This report has already been reviewed.")
        return redirect('view_weekly_report', report_id=report.id)

    if request.method == 'POST':
        form = ProgressReportRejectionForm(request.POST)

        if form.is_valid():
            try:
                reason = form.cleaned_data['rejection_reason']

                # Reject the report
                report.reject(reviewer=request.user.userprofile, reason=reason)

                # Toast message for rejection success
                set_toast_message(
                    request,
                    f"Progress report #{report.report_number} rejected successfully. PM has been notified.",
                    "success"
                )

                messages.success(
                    request,
                    f"Progress report rejected. PM has been notified: {reason[:100]}..."
                )

                # Notify PM that their report was rejected
                from notifications.models import Notification, NotificationStatus
                notification = Notification.objects.create(
                    message=f"Your weekly progress report for {report.project.project_name} was rejected: {reason[:80]}... (Week: {report.week_start_date.strftime('%b %d')} - {report.week_end_date.strftime('%b %d, %Y')})",
                    link=f"/scheduling/progress/weekly/{report.id}/",
                    role='PM'
                )
                NotificationStatus.objects.create(
                    notification=notification,
                    user=report.submitted_by,
                    is_read=False
                )

                # Send email notification to PM
                from notifications.email_utils import send_progress_report_rejected_email, get_site_url

                domain = get_site_url()
                send_progress_report_rejected_email(
                    pm_user=report.submitted_by.user,
                    report=report,
                    rejector_name=request.user.userprofile.full_name,
                    rejection_reason=reason,
                    domain=domain
                )

                return redirect('review_weekly_reports')

            except Exception as e:
                logger.error(f"Error rejecting report: {str(e)}")
                messages.error(request, f"Error rejecting report: {str(e)}")
        else:
            messages.error(request, "Please provide a valid rejection reason.")

    else:
        form = ProgressReportRejectionForm()

    context = {
        'report': report,
        'form': form,
    }

    return render(request, 'scheduling/weekly_progress/reject_report.html', context)


@login_required
def download_report_excel(request, report_id):
    """Download the submitted Excel file from a progress report"""
    report = get_object_or_404(WeeklyProgressReport, id=report_id)

    # Check if Excel file exists
    if not report.excel_file or not report.excel_file.name:
        messages.error(request, "No Excel file available for this report.")
        return redirect('view_weekly_report', report_id=report.id)

    try:
        # Get the file
        excel_file = report.excel_file

        # Create response with file content
        response = HttpResponse(
            excel_file.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        # Extract filename from path or use default
        import os
        filename = os.path.basename(excel_file.name)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        logger.info(f"Downloaded Excel file for report #{report.report_number}")
        return response

    except Exception as e:
        logger.error(f"Error downloading Excel file: {str(e)}")
        messages.error(request, f"Error downloading Excel file: {str(e)}")
        return redirect('view_weekly_report', report_id=report.id)


@login_required
def export_report_excel(request, report_id):
    """Export a single weekly progress report to Excel"""
    report = get_object_or_404(WeeklyProgressReport, id=report_id)

    try:
        # Generate Excel file
        wb = export_weekly_report_to_excel(report)

        # Create response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        # Set filename
        filename = f"Progress_Report_{report.report_number}_{report.week_start_date.strftime('%Y%m%d')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # Save workbook to response
        wb.save(response)

        logger.info(f"Excel export successful for report #{report.report_number}")
        return response

    except Exception as e:
        logger.error(f"Error exporting report to Excel: {str(e)}")
        messages.error(request, f"Error exporting to Excel: {str(e)}")
        return redirect('view_weekly_report', report_id=report.id)


@login_required
def export_project_reports_excel(request, project_id):
    """Export all progress reports for a project to Excel (multiple sheets)"""
    project = get_object_or_404(ProjectProfile, id=project_id)

    # Get filter parameters - support both GET and POST
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            status_filter = data.get('status', 'A')
        except:
            start_date = None
            end_date = None
            status_filter = 'A'
    else:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        status_filter = request.GET.get('status', 'A')  # Default: approved only

    # Get reports
    reports = WeeklyProgressReport.objects.filter(project=project)

    # Apply date filter - check for overlap with the selected range
    # A report overlaps if: report_start <= range_end AND report_end >= range_start
    if start_date and end_date:
        from django.db.models import Q
        reports = reports.filter(
            Q(week_start_date__lte=end_date) & Q(week_end_date__gte=start_date)
        )

    # Apply status filter
    if status_filter != 'all':
        reports = reports.filter(status=status_filter)

    reports = reports.order_by('week_start_date')

    if not reports.exists():
        error_msg = "No reports available to export for the selected criteria. Please adjust your filters or ensure reports have been submitted."
        if request.method == 'POST':
            return JsonResponse({
                'error': error_msg,
                'suggestion': 'Try changing your date range or status filter.'
            }, status=404)

        from authentication.utils.toast_helpers import set_toast_message
        set_toast_message(request, error_msg, "warning")
        return redirect('list_weekly_reports', project_id=project.id)

    try:
        # Generate Excel file with multiple sheets
        wb = export_multiple_reports_to_excel(reports)

        # Create response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        # Set filename
        filename = f"{project.project_id}_Progress_Reports_{datetime.now().strftime('%Y%m%d')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # Save workbook to response
        wb.save(response)

        logger.info(f"Excel export successful for project {project.project_id} - {reports.count()} reports")
        return response

    except Exception as e:
        logger.error(f"Error exporting project reports to Excel: {str(e)}")
        import traceback
        traceback.print_exc()
        if request.method == 'POST':
            return HttpResponse(f"Error exporting to Excel: {str(e)}", status=500)
        messages.error(request, f"Error exporting to Excel: {str(e)}")
        return redirect('list_weekly_reports', project_id=project.id)


@login_required
@require_http_methods(['GET', 'POST'])
def export_project_reports_pdf(request, project_id):
    """Export progress reports to PDF"""
    try:
        if not WEASY_PRINT_AVAILABLE:
            error_msg = 'PDF export not available - WeasyPrint library not installed'
            if request.method == 'POST':
                return JsonResponse({'error': error_msg}, status=500)
            messages.error(request, error_msg)
            return redirect('list_weekly_reports', project_id=project.id)

        project = get_object_or_404(ProjectProfile, id=project_id)

        # Get POST data
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                start_date = data.get('start_date')
                end_date = data.get('end_date')
                status_filter = data.get('status', 'A')
                include_options = data.get('includeOptions', {})
                logger.info(f"PDF Export - Received data: {data}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}")
                return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        else:
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            status_filter = request.GET.get('status', 'A')
            include_options = {
                'summary_table': True,
                'project_header': True,
                'status_summary': True,
                'totals': True
            }

        # Get reports
        reports = WeeklyProgressReport.objects.filter(project=project)
        logger.info(f"PDF Export - Total reports for project: {reports.count()}")

        # Apply date filter - check for overlap with the selected range
        # A report overlaps if: report_start <= range_end AND report_end >= range_start
        if start_date and end_date:
            from django.db.models import Q
            reports = reports.filter(
                Q(week_start_date__lte=end_date) & Q(week_end_date__gte=start_date)
            )
            logger.info(f"PDF Export - After date filter ({start_date} to {end_date}): {reports.count()}")

        # Apply status filter
        if status_filter != 'all':
            reports = reports.filter(status=status_filter)
            logger.info(f"PDF Export - After status filter ({status_filter}): {reports.count()}")

        reports = reports.order_by('week_start_date')

        if not reports.exists():
            # Create a helpful error message based on the filters
            if status_filter == 'all':
                error_msg = "No reports found for the selected date range. Try selecting a different time period or check if any reports have been submitted yet."
            elif status_filter == 'A':
                error_msg = "No approved reports found for the selected period. Try changing the status filter or check if reports need approval first."
            elif status_filter == 'P':
                error_msg = "No pending reports found for the selected period. All reports may have already been reviewed."
            elif status_filter == 'R':
                error_msg = "No rejected reports found for the selected period."
            else:
                error_msg = f"No reports found for the selected period (status={status_filter})"

            logger.warning(error_msg)
            if request.method == 'POST':
                return JsonResponse({
                    'error': error_msg,
                    'suggestion': 'Try adjusting your date range or status filter to find reports.'
                }, status=404)

            from authentication.utils.toast_helpers import set_toast_message
            set_toast_message(request, error_msg, "warning")
            return redirect('list_weekly_reports', project_id=project.id)

        # Calculate statistics
        approved_count = reports.filter(status='A').count()
        pending_count = reports.filter(status='P').count()
        rejected_count = reports.filter(status='R').count()

        # Calculate totals
        total_period_amount = sum(r.total_period_amount for r in reports)
        total_cumulative_amount = reports.last().cumulative_project_amount if reports.exists() else 0
        latest_period_percent = reports.last().total_period_percent if reports.exists() else 0
        latest_cumulative_percent = reports.last().cumulative_project_percent if reports.exists() else 0

        # Get logo path
        logo_path = os.path.join(settings.STATIC_ROOT or settings.BASE_DIR, 'powermason_capstone', 'static', 'img', 'powermason_logo.png')
        if not os.path.exists(logo_path):
            logo_path = os.path.join(settings.BASE_DIR, 'powermason_capstone', 'static', 'img', 'powermason_logo.png')
        logo_url = f'file:///{logo_path.replace(os.sep, "/")}' if os.path.exists(logo_path) else None

        # Get Philippines time
        ph_tz = pytz.timezone('Asia/Manila')
        ph_time = timezone.now().astimezone(ph_tz)

        # Prepare context
        context = {
            'project': project,
            'reports': reports,
            'approved_count': approved_count,
            'pending_count': pending_count,
            'rejected_count': rejected_count,
            'total_period_amount': total_period_amount,
            'total_cumulative_amount': total_cumulative_amount,
            'latest_period_percent': latest_period_percent,
            'latest_cumulative_percent': latest_cumulative_percent,
            'generated_date': ph_time.strftime('%B %d, %Y %I:%M %p') + ' (PHT)',
            'generated_by': request.user.get_full_name() or request.user.username,
            'logo_path': logo_url,
            'include_summary_table': include_options.get('summary_table', True),
            'include_project_header': include_options.get('project_header', True),
            'include_status_summary': include_options.get('status_summary', True),
            'include_totals': include_options.get('totals', True),
        }

        if start_date and end_date:
            context['date_range'] = {
                'start': datetime.strptime(start_date, '%Y-%m-%d').date(),
                'end': datetime.strptime(end_date, '%Y-%m-%d').date()
            }

        # Render template
        html_string = render_to_string('scheduling/weekly_progress/reports_pdf.html', context)

        # Generate PDF with error handling
        try:
            pdf = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()
        except Exception as pdf_error:
            # Import debug helper from cost_export_views
            from project_profiling.cost_export_views import render_pdf_error_debug
            return render_pdf_error_debug(request, project_id, pdf_error, 'Weekly Progress PDF Generation')

        # Create response
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"{project.project_id}_Progress_Report_{start_date or 'All'}_to_{end_date or 'All'}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        # Import debug helper for general errors
        from project_profiling.cost_export_views import render_pdf_error_debug
        return render_pdf_error_debug(request, project_id if 'project_id' in locals() else None, e, 'Weekly Progress General')


@login_required
def print_project_reports(request, project_id):
    """Generate print preview for progress reports"""
    try:
        project = get_object_or_404(ProjectProfile, id=project_id)

        # Get GET parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        status_filter = request.GET.get('status', 'A')
        include_summary = request.GET.get('include_summary', 'true') == 'true'
        include_header = request.GET.get('include_header', 'true') == 'true'
        include_status = request.GET.get('include_status', 'true') == 'true'
        include_totals = request.GET.get('include_totals', 'true') == 'true'

        # Get reports
        reports = WeeklyProgressReport.objects.filter(project=project)

        # Apply date filter
        if start_date and end_date:
            reports = reports.filter(
                week_start_date__gte=start_date,
                week_end_date__lte=end_date
            )

        # Apply status filter
        if status_filter != 'all':
            reports = reports.filter(status=status_filter)

        reports = reports.order_by('week_start_date')

        # Calculate statistics
        approved_count = reports.filter(status='A').count()
        pending_count = reports.filter(status='P').count()
        rejected_count = reports.filter(status='R').count()

        # Calculate totals
        total_period_amount = sum(r.total_period_amount for r in reports)
        total_cumulative_amount = reports.last().cumulative_project_amount if reports.exists() else 0
        latest_period_percent = reports.last().total_period_percent if reports.exists() else 0
        latest_cumulative_percent = reports.last().cumulative_project_percent if reports.exists() else 0

        # Get Philippines time
        ph_tz = pytz.timezone('Asia/Manila')
        ph_time = timezone.now().astimezone(ph_tz)

        # Get logo path
        logo_path = os.path.join(settings.BASE_DIR, 'powermason_capstone', 'static', 'img', 'powermason_logo.png')
        logo_url = request.build_absolute_uri(settings.STATIC_URL + 'img/powermason_logo.png') if os.path.exists(logo_path) else None

        # Prepare context
        context = {
            'project': project,
            'reports': reports,
            'approved_count': approved_count,
            'pending_count': pending_count,
            'rejected_count': rejected_count,
            'total_period_amount': total_period_amount,
            'total_cumulative_amount': total_cumulative_amount,
            'latest_period_percent': latest_period_percent,
            'latest_cumulative_percent': latest_cumulative_percent,
            'generated_date': ph_time.strftime('%B %d, %Y %I:%M %p') + ' (PHT)',
            'logo_url': logo_url,
            'include_summary': include_summary,
            'include_header': include_header,
            'include_status': include_status,
            'include_totals': include_totals,
        }

        if start_date and end_date:
            context['date_range'] = {
                'start': datetime.strptime(start_date, '%Y-%m-%d').date(),
                'end': datetime.strptime(end_date, '%Y-%m-%d').date()
            }

        return render(request, 'scheduling/weekly_progress/reports_print.html', context)

    except Exception as e:
        logger.error(f"Error generating print preview: {str(e)}")
        messages.error(request, f"Error generating print preview: {str(e)}")
        return redirect('list_weekly_reports', project_id=project.id)


@login_required
@role_required('PM')
def download_progress_template(request, project_id):
    """Download blank Excel template for offline progress entry"""
    project = get_object_or_404(ProjectProfile, id=project_id)

    # Get week dates from GET parameters
    week_start = request.GET.get('week_start')
    week_end = request.GET.get('week_end')

    if not week_start or not week_end:
        messages.error(request, "Please select week dates first")
        return redirect('submit_weekly_progress', project_id=project.id)

    try:
        week_start_date = datetime.strptime(week_start, '%Y-%m-%d').date()
        week_end_date = datetime.strptime(week_end, '%Y-%m-%d').date()

        # Generate template data
        template_data = generate_progress_template(project, week_start_date, week_end_date)

        # Check if there are any BOQ items
        divisions = template_data.get('divisions', [])
        total_boq_items = sum(len(div.get('boq_items', [])) for div in divisions)

        if total_boq_items == 0:
            messages.warning(
                request,
                f"No BOQ items found for this project. "
                f"Please ensure your project has BOQ data uploaded."
            )
            return redirect('submit_weekly_progress', project_id=project.id)

        # Generate Excel file (using V2 format)
        wb = generate_blank_template_v2(template_data)

        # Create response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        # Set filename: (PROJ_CODE)_PROGRESS_REPORT_(DATE).xlsx
        project_code = project.project_id if hasattr(project, 'project_id') and project.project_id else f"Project_{project.id}"
        filename = f"{project_code}_PROGRESS_REPORT_{week_start_date.strftime('%Y%m%d')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # Save workbook to response
        wb.save(response)

        logger.info(f"Excel template downloaded for project {project.id} - week {week_start_date} - {total_boq_items} BOQ items")
        return response

    except Exception as e:
        logger.error(f"Error generating Excel template: {str(e)}", exc_info=True)
        messages.error(request, f"Error generating template: {str(e)}")
        return redirect('submit_weekly_progress', project_id=project.id)


@login_required
@role_required('PM')
def upload_progress_excel(request, project_id):
    """Upload and process filled Excel progress report"""
    from authentication.utils.toast_helpers import set_toast_message
    from authentication.models import UserProfile

    project = get_object_or_404(ProjectProfile, id=project_id)

    if request.method != 'POST':
        set_toast_message(request, "Invalid request method", "error")
        return redirect('submit_weekly_progress', project_id=project.id)

    # Get uploaded Excel file
    excel_file = request.FILES.get('progress_excel')
    if not excel_file:
        set_toast_message(request, "Please select an Excel file to upload", "error")
        return redirect('submit_weekly_progress', project_id=project.id)

    # Validate file extension
    if not excel_file.name.endswith(('.xlsx', '.xls')):
        set_toast_message(request, "Please upload an Excel file (.xlsx or .xls)", "error")
        return redirect('submit_weekly_progress', project_id=project.id)

    # Get supporting files/images
    supporting_files = request.FILES.getlist('supporting_files')

    try:
        # Read and validate Excel file
        result = read_progress_excel(excel_file)

        if not result['success']:
            # Show errors using toast
            error_msg = "Excel file validation failed. Check: " + ", ".join(result['errors'][:3])
            set_toast_message(request, error_msg, "error")
            return redirect('submit_weekly_progress', project_id=project.id)

        # Get week dates from form
        week_start = request.POST.get('week_start_date')
        week_end = request.POST.get('week_end_date')
        remarks = request.POST.get('remarks', '')

        if not week_start or not week_end:
            set_toast_message(request, "Please select week dates before uploading", "error")
            return redirect('submit_weekly_progress', project_id=project.id)

        week_start_date = datetime.strptime(week_start, '%Y-%m-%d').date()
        week_end_date = datetime.strptime(week_end, '%Y-%m-%d').date()

        # Check if report already exists
        existing_report = WeeklyProgressReport.objects.filter(
            project=project,
            week_start_date=week_start_date
        ).first()

        if existing_report:
            # Allow resubmission only if the previous report was rejected
            if existing_report.status == 'R':
                # Delete the rejected report to allow new submission
                existing_report.delete()
                logger.info(f"Deleted rejected report {existing_report.id} to allow resubmission")
            else:
                status_display = existing_report.get_status_display()
                set_toast_message(
                    request,
                    f"Progress report already exists for week {week_start_date.strftime('%b %d')} - {week_end_date.strftime('%b %d, %Y')} (Status: {status_display}). Cannot submit duplicate report.",
                    "warning"
                )
                return redirect('submit_weekly_progress', project_id=project.id)

        # Create weekly report and BOQ items
        with transaction.atomic():
            # Create report
            report = WeeklyProgressReport.objects.create(
                project=project,
                week_start_date=week_start_date,
                week_end_date=week_end_date,
                remarks=remarks,
                submitted_by=request.user.userprofile,
                status='P',
                excel_file=excel_file
            )

            # Save supporting files/attachments
            from .models import WeeklyReportAttachment
            for supporting_file in supporting_files:
                WeeklyReportAttachment.objects.create(
                    weekly_report=report,
                    file=supporting_file,
                    filename=supporting_file.name,
                    file_size=supporting_file.size
                )

            # Create BOQ item progress records
            for boq_data in result['boq_items']:
                # Find the corresponding task
                task = ProjectTask.objects.filter(
                    project=project,
                    boq_item_codes__contains=[boq_data['boq_item_code']]
                ).first()

                if not task:
                    logger.warning(f"No task found for BOQ item {boq_data['boq_item_code']}")
                    continue

                BOQItemProgress.objects.create(
                    project=project,
                    weekly_report=report,
                    boq_item_code=boq_data['boq_item_code'],
                    description=boq_data['description'],
                    division=boq_data['division'],
                    task_group=boq_data['task_group'],
                    project_task=task,
                    approved_contract_amount=boq_data['approved_amount'],
                    quantity=boq_data['quantity'],
                    unit_of_measurement=boq_data['uom'],
                    cumulative_percent=boq_data['cumulative_percent'],
                    cumulative_amount=boq_data['cumulative_amount'],
                    previous_cumulative_percent=boq_data['previous_cumulative_percent'],
                    scheduled_start_date=task.start_date,
                    scheduled_end_date=task.end_date,
                    status='P',
                    reported_by=request.user.userprofile,
                    report_date=week_end_date,
                    remarks=boq_data['remarks'],
                    progress_decreased=boq_data['progress_decreased'],
                    decrease_reason=boq_data['remarks'] if boq_data['progress_decreased'] else ''
                )

            # Set report totals from Excel summary (don't use calculate_totals as it incorrectly sums percentages)
            weekly_progress_percent = result['summary']['total_period_percent']
            weekly_progress_amount = result['summary']['total_period_amount']

            # Calculate cumulative progress by adding all approved AND pending reports
            # (Include pending so users can see what cumulative will be)
            previous_reports = WeeklyProgressReport.objects.filter(
                project=project,
                status__in=['A', 'P'],  # Include both Approved and Pending
                week_end_date__lt=week_start_date
            ).order_by('-week_end_date')

            cumulative_amount = weekly_progress_amount
            if previous_reports.exists():
                total_previous_amount = sum(r.total_period_amount for r in previous_reports)
                cumulative_amount = total_previous_amount + weekly_progress_amount

            # Calculate cumulative percentage based on total project budget
            # Use the project's approved budget from database, NOT from Excel
            # (Excel only contains items with progress, not all BOQ items)
            total_approved_budget = project.approved_budget or 0
            if total_approved_budget > 0:
                # Calculate cumulative percent based on cumulative amount to ensure consistency
                cumulative_percent = Decimal(str(round((float(cumulative_amount) / float(total_approved_budget)) * 100, 2)))
            else:
                # Fallback: just add the period percentages
                cumulative_percent = weekly_progress_percent
                if previous_reports.exists():
                    total_previous_percent = sum(r.total_period_percent for r in previous_reports)
                    cumulative_percent = total_previous_percent + weekly_progress_percent

            report.total_period_amount = weekly_progress_amount
            report.total_period_percent = weekly_progress_percent
            report.cumulative_project_amount = cumulative_amount
            report.cumulative_project_percent = cumulative_percent
            report.save(update_fields=[
                'total_period_amount',
                'total_period_percent',
                'cumulative_project_amount',
                'cumulative_project_percent'
            ])

            # Validate against schedule
            warnings = report.validate_against_schedule()

            set_toast_message(
                request,
                f"Progress report submitted! Weekly Progress: {weekly_progress_percent:.2f}% (₱{weekly_progress_amount:,.2f}). {result['summary']['items_with_progress']} BOQ items processed.",
                "success"
            )

            # Create notification for PM (report submitted successfully)
            from notifications.models import Notification, NotificationStatus
            pm_notification = Notification.objects.create(
                message=f"Weekly progress report for {project.project_name} submitted successfully (Week: {week_start_date.strftime('%b %d')} - {week_end_date.strftime('%b %d, %Y')})",
                link=f"/scheduling/progress/weekly/{report.id}/",
                role='PM'
            )
            NotificationStatus.objects.create(
                notification=pm_notification,
                user=request.user.userprofile,
                is_read=False
            )

            # Create notification for OM/EG users (new report needs review)
            om_eg_notification = Notification.objects.create(
                message=f"New weekly progress report from {project.project_name} needs review (Week: {week_start_date.strftime('%b %d')} - {week_end_date.strftime('%b %d, %Y')})",
                link=f"/scheduling/progress/weekly/{report.id}/",
                role='OM'  # Both OM and EG will see this
            )

            # Add notification for all OM and EG users
            om_eg_users = UserProfile.objects.filter(role__in=['OM', 'EG'])
            for user_profile in om_eg_users:
                NotificationStatus.objects.create(
                    notification=om_eg_notification,
                    user=user_profile,
                    is_read=False
                )

            # Send email notifications
            from notifications.email_utils import (
                send_progress_report_submitted_email,
                send_progress_report_pending_email,
                get_site_url
            )

            domain = get_site_url()

            # Email to PM (confirmation)
            send_progress_report_submitted_email(
                pm_user=request.user,
                report=report,
                domain=domain
            )

            # Email to OM/EG users (pending review)
            if om_eg_users.exists():
                send_progress_report_pending_email(
                    om_eg_users=om_eg_users,
                    report=report,
                    pm_name=request.user.userprofile.full_name,
                    domain=domain
                )

            logger.info(f"Progress report submitted: Project {project.id}, Week {week_start_date}")
            return redirect('view_weekly_report', report_id=report.id)

    except Exception as e:
        logger.error(f"Error processing Excel upload: {str(e)}")
        set_toast_message(request, f"Error processing Excel file: {str(e)}", "error")
        return redirect('submit_weekly_progress', project_id=project.id)
