# ========================================
# COST TRACKING VIEWS - WEEK 3
# Subcontractor Management & Mobilization Costs
# ========================================

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum
from django.utils.timezone import localtime
from decimal import Decimal

from authentication.utils.decorators import verified_email_required, role_required
from authentication.utils.tokens import get_user_profile, verify_user_profile
from .models import (
    ProjectProfile, SubcontractorExpense, SubcontractorPayment
)


# ========================================
# SUBCONTRACTOR MANAGEMENT
# ========================================

@login_required
@verified_email_required
def subcontractor_list(request):
    """Display subcontractor management page"""
    return render(request, 'project_profiling/subcontractor_list.html')


@login_required
@verified_email_required
def api_subcontractor_list(request):
    """API endpoint to get list of subcontractors or create new one"""
    import json

    try:
        user_profile = request.user.userprofile

        # POST - Create new subcontractor
        if request.method == 'POST':
            if user_profile.role not in ['EG', 'OM']:
                return JsonResponse({'error': 'Unauthorized'}, status=403)

            data = json.loads(request.body)

            # Validate required fields
            required_fields = ['project_id', 'subcontractor_name', 'contact_person',
                             'contact_number', 'contract_number', 'contract_amount', 'scope_of_work']
            missing = [f for f in required_fields if not data.get(f)]
            if missing:
                return JsonResponse({'error': f'Missing fields: {", ".join(missing)}'}, status=400)

            # Create subcontractor
            project = get_object_or_404(ProjectProfile, id=data.get('project_id'))

            subcon = SubcontractorExpense.objects.create(
                project=project,
                subcontractor_name=data.get('subcontractor_name'),
                contact_person=data.get('contact_person'),
                contact_number=data.get('contact_number'),
                contract_number=data.get('contract_number'),
                contract_amount=Decimal(data.get('contract_amount')),
                amount_paid=Decimal(data.get('amount_paid', 0)),
                status=data.get('status', 'PEND'),
                scope_of_work=data.get('scope_of_work')
            )

            return JsonResponse({
                'success': True,
                'message': 'Subcontractor created successfully',
                'subcontractor_id': subcon.id
            })

        # GET - List subcontractors
        else:
            # Get subcontractors based on role
            if user_profile.role in ['EG', 'OM']:
                subcontractors = SubcontractorExpense.objects.select_related('project').all()
            elif user_profile.role == 'PM':
                subcontractors = SubcontractorExpense.objects.select_related('project').filter(
                    project__project_manager=user_profile
                )
            else:
                subcontractors = SubcontractorExpense.objects.none()

            # Format response
            data = []
            for subcon in subcontractors:
                data.append({
                    'id': subcon.id,
                    'subcontractor_name': subcon.subcontractor_name,
                    'project_name': subcon.project.project_name,
                    'project_id': subcon.project.id,  # Numeric ID for filtering
                    'project_code': subcon.project.project_id,  # String code for display
                    'contract_number': subcon.contract_number,
                    'contract_amount': float(subcon.contract_amount),
                    'amount_paid': float(subcon.amount_paid),
                    'remaining_balance': float(subcon.remaining_balance),
                    'payment_percentage': float(subcon.payment_percentage),
                    'status': subcon.status,
                    'status_display': subcon.get_status_display(),
                    'contact_person': subcon.contact_person,
                    'contact_number': subcon.contact_number,
                    'scope_of_work': subcon.scope_of_work,
                    'start_date': subcon.start_date.isoformat() if subcon.start_date else None,
                })

            # Calculate stats
            total_subcontractors = subcontractors.count()
            active_contracts = subcontractors.filter(status='PROG').count()
            total_contract_value = subcontractors.aggregate(total=Sum('contract_amount'))['total'] or 0
            total_paid = subcontractors.aggregate(total=Sum('amount_paid'))['total'] or 0

            return JsonResponse({
                'subcontractors': data,
                'stats': {
                    'total_subcontractors': total_subcontractors,
                    'active_contracts': active_contracts,
                    'total_contract_value': float(total_contract_value),
                    'total_paid': float(total_paid),
                }
            })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@verified_email_required
def api_subcontractor_detail(request, subcon_id):
    """Handle GET, POST (update), DELETE for a specific subcontractor"""
    import json

    try:
        user_profile = request.user.userprofile

        # Check permissions
        if user_profile.role in ['EG', 'OM']:
            subcon = get_object_or_404(SubcontractorExpense, id=subcon_id)
        elif user_profile.role == 'PM':
            subcon = get_object_or_404(
                SubcontractorExpense,
                id=subcon_id,
                project__project_manager=user_profile
            )
        else:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        # GET - Retrieve details
        if request.method == 'GET':
            data = {
                'id': subcon.id,
                'name': subcon.subcontractor_name,
                'contact_person': subcon.contact_person,
                'contact_number': subcon.contact_number,
                'project_name': subcon.project.project_name,
                'project_id': subcon.project.id,
                'contract_number': subcon.contract_number,
                'scope_of_work': subcon.scope_of_work,
                'contract_amount': float(subcon.contract_amount),
                'amount_paid': float(subcon.amount_paid),
                'remaining_balance': float(subcon.remaining_balance),
                'payment_percentage': float(subcon.payment_percentage),
                'status': subcon.status,
                'status_display': subcon.get_status_display(),
                'start_date': subcon.start_date.isoformat() if subcon.start_date else None,
                'end_date': subcon.end_date.isoformat() if subcon.end_date else None,
                'completion_date': subcon.completion_date.isoformat() if subcon.completion_date else None,
                'notes': subcon.notes,
            }
            return JsonResponse(data)

        # POST - Update subcontractor
        elif request.method == 'POST':
            if user_profile.role not in ['EG', 'OM']:
                return JsonResponse({'error': 'Unauthorized'}, status=403)

            data = json.loads(request.body)

            # Update fields
            project = get_object_or_404(ProjectProfile, id=data.get('project_id'))
            subcon.project = project
            subcon.subcontractor_name = data.get('subcontractor_name', subcon.subcontractor_name)
            subcon.contact_person = data.get('contact_person', subcon.contact_person)
            subcon.contact_number = data.get('contact_number', subcon.contact_number)
            subcon.contract_number = data.get('contract_number', subcon.contract_number)
            subcon.contract_amount = Decimal(data.get('contract_amount', subcon.contract_amount))
            subcon.amount_paid = Decimal(data.get('amount_paid', subcon.amount_paid))
            subcon.status = data.get('status', subcon.status)
            subcon.scope_of_work = data.get('scope_of_work', subcon.scope_of_work)
            subcon.save()

            return JsonResponse({
                'success': True,
                'message': 'Subcontractor updated successfully'
            })

        # DELETE - Delete subcontractor
        elif request.method == 'DELETE':
            if user_profile.role not in ['EG', 'OM']:
                return JsonResponse({'error': 'Unauthorized'}, status=403)

            subcon.delete()
            return JsonResponse({
                'success': True,
                'message': 'Subcontractor deleted successfully'
            })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@verified_email_required
@require_http_methods(["GET"])
def api_subcontractor_payments(request, subcon_id):
    """Get payment history for a subcontractor"""
    try:
        user_profile = request.user.userprofile

        if user_profile.role in ['EG', 'OM']:
            subcon = get_object_or_404(SubcontractorExpense, id=subcon_id)
        elif user_profile.role == 'PM':
            subcon = get_object_or_404(
                SubcontractorExpense,
                id=subcon_id,
                project__project_manager=user_profile
            )
        else:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        payments = SubcontractorPayment.objects.filter(subcontractor_expense=subcon).order_by('-payment_date')

        data = []
        for payment in payments:
            data.append({
                'id': payment.id,
                'payment_number': payment.payment_number,
                'milestone_description': payment.milestone_description,
                'amount': float(payment.amount),
                'payment_method': payment.payment_method,
                'payment_method_display': payment.get_payment_method_display(),
                'payment_date': payment.payment_date.isoformat(),
                'reference_number': payment.reference_number,
                'status': payment.status,
                'status_display': payment.get_status_display(),
                'approved_by': payment.approved_by.full_name if payment.approved_by else None,
                'created_at': localtime(payment.created_at).strftime('%b %d, %Y'),
            })

        return JsonResponse({'payments': data})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@verified_email_required
@require_http_methods(["POST"])
@role_required('EG', 'OM')
def api_create_payment(request, subcon_id):
    """Create a new payment for a subcontractor"""
    import json

    try:
        user_profile = request.user.userprofile
        subcon = get_object_or_404(SubcontractorExpense, id=subcon_id)

        # Get JSON data
        data = json.loads(request.body)

        milestone_description = data.get('milestone_description', '').strip()
        amount = data.get('amount')
        payment_method = data.get('payment_method', 'BANK')
        payment_date = data.get('payment_date')
        reference_number = data.get('reference_number', '').strip()
        notes = data.get('notes', '').strip()

        # Validate
        if not all([milestone_description, amount, payment_date]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        # Create payment
        payment = SubcontractorPayment.objects.create(
            subcontractor_expense=subcon,
            milestone_description=milestone_description,
            amount=Decimal(amount),
            payment_method=payment_method,
            payment_date=payment_date,
            reference_number=reference_number,
            notes=notes,
            status='PEND',  # Pending approval
            created_by=user_profile
        )

        # Update subcontractor amount_paid
        subcon.amount_paid += Decimal(amount)
        subcon.save()

        return JsonResponse({
            'success': True,
            'message': 'Payment created successfully',
            'payment_id': payment.id
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ========================================
# WEEKLY COST REPORT API VIEWS
# ========================================

from .models import WeeklyCostReport
from datetime import datetime, timedelta
from django.db.models import Q
from collections import defaultdict
import calendar


@login_required
@verified_email_required
@role_required('EG', 'OM')
def api_weekly_cost_reports(request, project_id):
    """
    GET: List all weekly cost reports for a project with optional date filtering
    Returns weekly reports, monthly summary, and totals
    """
    try:
        project = get_object_or_404(ProjectProfile, id=project_id)
        user_profile = request.user.userprofile

        # Check permissions
        if user_profile.role == 'PM' and project.project_manager != user_profile:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        # Get query parameters for filtering
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        period = request.GET.get('period')  # weekly, monthly, quarterly, yearly

        # Base queryset
        reports = WeeklyCostReport.objects.filter(project=project)

        # Apply date filters
        if start_date and end_date:
            reports = reports.filter(
                period_start__gte=start_date,
                period_end__lte=end_date
            )
        elif period:
            # Calculate date range based on period
            today = datetime.now().date()
            if period == 'this_week':
                start_of_week = today - timedelta(days=today.weekday())
                end_of_week = start_of_week + timedelta(days=6)
                reports = reports.filter(
                    period_start__gte=start_of_week,
                    period_end__lte=end_of_week
                )
            elif period == 'this_month':
                start_of_month = today.replace(day=1)
                last_day = calendar.monthrange(today.year, today.month)[1]
                end_of_month = today.replace(day=last_day)
                reports = reports.filter(
                    period_start__gte=start_of_month,
                    period_end__lte=end_of_month
                )
            elif period == 'this_quarter':
                quarter = (today.month - 1) // 3
                start_of_quarter = datetime(today.year, quarter * 3 + 1, 1).date()
                end_month = quarter * 3 + 3
                last_day = calendar.monthrange(today.year, end_month)[1]
                end_of_quarter = datetime(today.year, end_month, last_day).date()
                reports = reports.filter(
                    period_start__gte=start_of_quarter,
                    period_end__lte=end_of_quarter
                )
            elif period == 'this_year':
                start_of_year = datetime(today.year, 1, 1).date()
                end_of_year = datetime(today.year, 12, 31).date()
                reports = reports.filter(
                    period_start__gte=start_of_year,
                    period_end__lte=end_of_year
                )
            elif period == 'last_30_days':
                start_date_30 = today - timedelta(days=30)
                reports = reports.filter(
                    period_start__gte=start_date_30,
                    period_end__lte=today
                )

        # Format weekly reports
        weekly_reports = []
        for report in reports:
            weekly_reports.append({
                'id': report.id,
                'report_date': report.report_date.strftime('%Y-%m-%d'),
                'period_start': report.period_start.strftime('%Y-%m-%d'),
                'period_end': report.period_end.strftime('%Y-%m-%d'),
                'period_label': report.period_label,
                'genreq_amount': float(report.genreq_amount),
                'materials_amount': float(report.materials_amount),
                'labor_amount': float(report.labor_amount),
                'equipment_amount': float(report.equipment_amount),
                'total_amount': float(report.total_amount),
                'status': report.status,
                'submitted_by': report.submitted_by.full_name if report.submitted_by else None,
                'submitted_at': localtime(report.submitted_at).strftime('%b %d, %Y %I:%M %p'),
            })

        # Aggregate monthly summary
        monthly_summary = aggregate_monthly_data(reports)

        # Calculate grand totals
        totals = calculate_totals(reports)

        return JsonResponse({
            'success': True,
            'weekly_reports': weekly_reports,
            'monthly_summary': monthly_summary,
            'totals': totals,
            'report_count': reports.count()
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@verified_email_required
@require_http_methods(['POST'])
@role_required('EG', 'OM', 'PM')
def api_create_weekly_cost_report(request, project_id):
    """
    POST: Create a new weekly cost report
    """
    import json

    try:
        project = get_object_or_404(ProjectProfile, id=project_id)
        user_profile = request.user.userprofile

        # Check permissions
        if user_profile.role == 'PM' and project.project_manager != user_profile:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        # Parse request data
        data = json.loads(request.body)

        # Validate required fields
        required_fields = ['report_date', 'period_start', 'period_end']
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return JsonResponse({
                'error': f'Missing required fields: {", ".join(missing)}'
            }, status=400)

        # Check for duplicate period
        existing = WeeklyCostReport.objects.filter(
            project=project,
            period_start=data.get('period_start'),
            period_end=data.get('period_end')
        ).exists()

        if existing:
            return JsonResponse({
                'error': 'A report for this period already exists'
            }, status=400)

        # Create the report
        report = WeeklyCostReport.objects.create(
            project=project,
            report_date=data.get('report_date'),
            period_start=data.get('period_start'),
            period_end=data.get('period_end'),
            genreq_amount=Decimal(data.get('genreq_amount', 0)),
            materials_amount=Decimal(data.get('materials_amount', 0)),
            labor_amount=Decimal(data.get('labor_amount', 0)),
            equipment_amount=Decimal(data.get('equipment_amount', 0)),
            status='pending',
            submitted_by=user_profile,
            remarks=data.get('remarks', '')
        )

        return JsonResponse({
            'success': True,
            'message': 'Weekly cost report created successfully',
            'report_id': report.id,
            'total_amount': float(report.total_amount)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def aggregate_monthly_data(reports):
    """
    Helper function to aggregate weekly reports into monthly summary
    """
    monthly_data = defaultdict(lambda: {
        'genreq': 0,
        'materials': 0,
        'labor': 0,
        'equipment': 0,
        'total': 0
    })

    for report in reports:
        month_key = report.period_start.strftime('%B %Y')  # e.g., "June 2024"
        monthly_data[month_key]['genreq'] += float(report.genreq_amount)
        monthly_data[month_key]['materials'] += float(report.materials_amount)
        monthly_data[month_key]['labor'] += float(report.labor_amount)
        monthly_data[month_key]['equipment'] += float(report.equipment_amount)
        monthly_data[month_key]['total'] += float(report.total_amount)

    # Convert to sorted list
    monthly_summary = []
    for month, data in sorted(monthly_data.items(), key=lambda x: datetime.strptime(x[0], '%B %Y')):
        monthly_summary.append({
            'month': month,
            'genreq': data['genreq'],
            'materials': data['materials'],
            'labor': data['labor'],
            'equipment': data['equipment'],
            'total': data['total']
        })

    return monthly_summary


def calculate_totals(reports):
    """
    Helper function to calculate grand totals across all reports
    """
    totals = {
        'genreq': 0,
        'materials': 0,
        'labor': 0,
        'equipment': 0,
        'total': 0
    }

    for report in reports:
        totals['genreq'] += float(report.genreq_amount)
        totals['materials'] += float(report.materials_amount)
        totals['labor'] += float(report.labor_amount)
        totals['equipment'] += float(report.equipment_amount)
        totals['total'] += float(report.total_amount)

    return totals


