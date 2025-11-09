# ========================================
# ENHANCED COST TRACKING DASHBOARD
# Complete cost monitoring and expense management
# ========================================

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Q, F, DecimalField, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta

from authentication.utils.decorators import verified_email_required, role_required
from authentication.utils.tokens import get_user_profile, verify_user_profile
from .models import (
    ProjectProfile, ProjectBudget, FundAllocation, Expense,
    ProjectCost, SubcontractorExpense, CostCategory
)


@login_required
@verified_email_required
@role_required('EG', 'OM', 'PM')
def project_detail_cost_dashboard(request, project_id):
    """
    Detailed cost tracking dashboard for a specific project.
    Shows Budget vs Actual, Category breakdown, Expense history, Alerts
    """
    verified_profile = get_user_profile(request)
    if not verified_profile:
        return redirect("unauthorized")

    project = get_object_or_404(ProjectProfile, id=project_id)

    # Check permissions - PM can only see their projects
    if verified_profile.role == 'PM' and project.project_manager != verified_profile:
        return render(request, 'errors/403.html', status=403)

    # ========================================
    # 1. BUDGET OVERVIEW
    # ========================================

    # Total Planned Budget (from ProjectBudget)
    total_planned = project.budgets.aggregate(
        total=Sum('planned_amount')
    )['total'] or Decimal('0')

    # Total Allocated (from FundAllocation)
    total_allocated = FundAllocation.objects.filter(
        project_budget__project=project,
        is_deleted=False
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Total Actual Spending (from Expense)
    total_spent = Expense.objects.filter(
        project=project
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Total Disbursed Amount (includes weekly cost reports + subcontractor payments)
    from project_profiling.models import WeeklyCostReport

    # Get total from all weekly cost reports (all submitted reports)
    total_weekly_costs = WeeklyCostReport.objects.filter(
        project=project
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

    # Get total from subcontractor payments (amount_paid field)
    total_subcontractor_paid = SubcontractorExpense.objects.filter(
        project=project
    ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')

    # Total disbursed is weekly costs + subcontractor payments
    total_disbursed = total_weekly_costs + total_subcontractor_paid

    # Calculate key metrics using total disbursed
    remaining_budget = total_allocated - total_disbursed
    budget_utilization = (total_disbursed / total_allocated * 100) if total_allocated > 0 else 0
    is_over_budget = total_disbursed > total_allocated

    # Budget status
    if budget_utilization >= 90:
        budget_status = 'CRITICAL'
        budget_status_color = 'red'
    elif budget_utilization >= 75:
        budget_status = 'WARNING'
        budget_status_color = 'yellow'
    else:
        budget_status = 'HEALTHY'
        budget_status_color = 'green'

    # ========================================
    # 2. CATEGORY BREAKDOWN
    # ========================================

    categories_data = []
    for budget in project.budgets.select_related('scope').all():
        # Calculate allocated amount for this category
        allocated = budget.allocations.filter(
            is_deleted=False
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Calculate spent amount for this category
        spent = budget.expenses.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        # Calculate percentage
        utilization = (spent / allocated * 100) if allocated > 0 else 0

        categories_data.append({
            'scope': budget.scope.name,
            'category': budget.get_category_display(),
            'planned': budget.planned_amount,
            'allocated': allocated,
            'spent': spent,
            'remaining': allocated - spent,
            'utilization': utilization,
            'is_over': spent > allocated,
        })

    # ========================================
    # 3. RECENT EXPENSES
    # ========================================

    recent_expenses = Expense.objects.filter(
        project=project
    ).select_related(
        'budget_category__scope', 'created_by__user'
    ).order_by('-expense_date', '-created_at')[:10]

    # ========================================
    # 4. SPENDING TREND (Last 6 months)
    # ========================================

    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_spending = []

    for i in range(6):
        month_date = timezone.now() - timedelta(days=30 * i)
        month_start = month_date.replace(day=1)
        next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)

        spent_in_month = Expense.objects.filter(
            project=project,
            expense_date__gte=month_start,
            expense_date__lt=next_month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        monthly_spending.append({
            'month': month_start.strftime('%b %Y'),
            'amount': float(spent_in_month)
        })

    monthly_spending.reverse()  # Oldest first

    # ========================================
    # 5. COST PERFORMANCE INDICATORS
    # ========================================

    # Burn Rate (average spending per day)
    if project.start_date:
        days_elapsed = (timezone.now().date() - project.start_date).days + 1
        burn_rate = total_spent / days_elapsed if days_elapsed > 0 else Decimal('0')

        # Projected completion cost
        if project.target_completion_date:
            total_days = (project.target_completion_date - project.start_date).days + 1
            projected_cost = burn_rate * total_days
        else:
            projected_cost = None
    else:
        burn_rate = None
        projected_cost = None
        days_elapsed = 0

    # Cost Performance Index (CPI) - Earned Value Management
    # CPI = Earned Value / Actual Cost
    # For now, we'll use progress as a proxy for earned value
    earned_value = (project.progress / 100) * total_allocated if total_allocated > 0 else Decimal('0')
    cpi = (earned_value / total_spent) if total_spent > 0 else Decimal('0')

    # CPI Interpretation
    if cpi >= 1.0:
        cpi_status = 'GOOD'  # Getting more value than cost
        cpi_color = 'green'
    elif cpi >= 0.9:
        cpi_status = 'FAIR'
        cpi_color = 'yellow'
    else:
        cpi_status = 'POOR'  # Overspending relative to progress
        cpi_color = 'red'

    # ========================================
    # 6. SUBCONTRACTOR & MOBILIZATION COSTS
    # ========================================

    subcontractor_total = SubcontractorExpense.objects.filter(
        project=project
    ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')

    # Mobilization costs are now handled by ProjectGeneralRequirement
    mobilization_total = Decimal('0')

    # ========================================
    # 7. ALERTS & WARNINGS
    # ========================================

    alerts = []

    # Budget utilization alerts
    if budget_utilization >= 90:
        alerts.append({
            'level': 'CRITICAL',
            'message': f'Budget utilization at {budget_utilization:.1f}% - Immediate action required!',
            'icon': 'exclamation-circle'
        })
    elif budget_utilization >= 75:
        alerts.append({
            'level': 'WARNING',
            'message': f'Budget utilization at {budget_utilization:.1f}% - Monitor closely',
            'icon': 'exclamation-triangle'
        })

    # Category over-budget alerts
    over_budget_categories = [cat for cat in categories_data if cat['is_over']]
    if over_budget_categories:
        for cat in over_budget_categories:
            overage = cat['spent'] - cat['allocated']
            alerts.append({
                'level': 'CRITICAL',
                'message': f'{cat["scope"]} > {cat["category"]} is over budget by ₱{overage:,.2f}',
                'icon': 'exclamation-circle'
            })

    # CPI alert
    if cpi < 0.9 and total_spent > 0:
        alerts.append({
            'level': 'WARNING',
            'message': f'Cost Performance Index ({cpi:.2f}) is below target - Project is overspending relative to progress',
            'icon': 'chart-line'
        })

    # Projected cost overrun
    if projected_cost and projected_cost > total_allocated:
        overrun = projected_cost - total_allocated
        alerts.append({
            'level': 'WARNING',
            'message': f'Projected to exceed budget by ₱{overrun:,.2f} at current burn rate',
            'icon': 'trending-up'
        })

    # ========================================
    # CONTEXT
    # ========================================

    context = {
        'role': verified_profile.role,
        'project': project,

        # Budget Overview
        'total_planned': total_planned,
        'total_allocated': total_allocated,
        'total_spent': total_spent,
        'total_disbursed': total_disbursed,  # Total disbursed amount
        'remaining_budget': remaining_budget,
        'budget_utilization': budget_utilization,
        'is_over_budget': is_over_budget,
        'budget_status': budget_status,
        'budget_status_color': budget_status_color,

        # Category Breakdown
        'categories_data': categories_data,

        # Recent Expenses
        'recent_expenses': recent_expenses,

        # Spending Trend
        'monthly_spending': monthly_spending,

        # Cost Performance
        'burn_rate': burn_rate,
        'projected_cost': projected_cost,
        'days_elapsed': days_elapsed,
        'earned_value': earned_value,
        'cpi': cpi,
        'cpi_status': cpi_status,
        'cpi_color': cpi_color,

        # Additional Costs
        'subcontractor_total': subcontractor_total,
        'mobilization_total': mobilization_total,

        # Alerts
        'alerts': alerts,

        # For dropdowns in expense form
        'budget_categories': project.budgets.select_related('scope').all(),
        'expense_types': Expense.EXPENSE_TYPES,
    }

    return render(request, 'project_profiling/project_cost_dashboard_detail.html', context)


@login_required
@verified_email_required
@require_http_methods(["GET"])
def api_project_cost_summary(request, project_id):
    """
    API endpoint for cost data (for charts/AJAX updates)
    """
    try:
        project = get_object_or_404(ProjectProfile, id=project_id)

        # Check permissions
        user_profile = request.user.userprofile
        if user_profile.role == 'PM' and project.project_manager != user_profile:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        # Budget vs Actual by Category
        category_data = []
        for budget in project.budgets.select_related('scope').all():
            allocated = budget.allocations.filter(
                is_deleted=False
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            spent = budget.expenses.aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0')

            category_data.append({
                'name': f"{budget.scope.name} - {budget.get_category_display()}",
                'allocated': float(allocated),
                'spent': float(spent),
            })

        return JsonResponse({
            'success': True,
            'category_data': category_data,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@verified_email_required
@require_http_methods(["POST"])
def api_add_quick_expense(request, project_id):
    """
    Quick expense entry API (for AJAX form submission)
    """
    import json

    try:
        user_profile = request.user.userprofile
        project = get_object_or_404(ProjectProfile, id=project_id)

        # Check permissions
        if user_profile.role not in ['EG', 'OM', 'PM']:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        if user_profile.role == 'PM' and project.project_manager != user_profile:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        # Get form data
        data = json.loads(request.body)

        budget_id = data.get('budget_category_id')
        expense_type = data.get('expense_type')
        amount = data.get('amount')
        vendor = data.get('vendor', '')
        receipt_number = data.get('receipt_number', '')
        expense_date = data.get('expense_date')
        description = data.get('description', '')

        # Validate
        if not all([budget_id, expense_type, amount, expense_date]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        budget_category = get_object_or_404(ProjectBudget, id=budget_id, project=project)

        # Check allocation
        total_allocated = budget_category.allocations.filter(
            is_deleted=False
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        if total_allocated == 0:
            return JsonResponse({
                'error': 'No funds allocated to this category. Please allocate funds first.'
            }, status=400)

        # Check if over-budget
        total_spent = budget_category.expenses.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

        new_total = total_spent + Decimal(amount)
        warning = None

        if new_total > total_allocated:
            overage = new_total - total_allocated
            warning = f'This expense will put the category over budget by ₱{overage:,.2f}'

        # Create expense
        expense = Expense.objects.create(
            project=project,
            budget_category=budget_category,
            expense_type=expense_type,
            amount=Decimal(amount),
            vendor=vendor,
            receipt_number=receipt_number,
            expense_date=expense_date,
            description=description,
            created_by=user_profile
        )

        return JsonResponse({
            'success': True,
            'message': 'Expense added successfully',
            'warning': warning,
            'expense_id': expense.id,
            'new_total_spent': float(new_total),
            'remaining': float(total_allocated - new_total)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
