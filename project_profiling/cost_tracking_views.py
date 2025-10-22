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


