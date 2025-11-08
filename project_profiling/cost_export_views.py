# ========================================
# WEEKLY COST REPORT EXPORT VIEWS
# PDF and Excel Export Functionality
# ========================================

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Sum
from datetime import datetime
import json
import base64
from io import BytesIO
from decimal import Decimal

from authentication.utils.decorators import verified_email_required, role_required
from .models import ProjectProfile, WeeklyCostReport
from .cost_tracking_views import aggregate_monthly_data, calculate_totals

# WeasyPrint for PDF generation
from weasyprint import HTML, CSS

# OpenPyXL for Excel generation
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as XLImage
from PIL import Image as PILImage


# ========================================
# PDF EXPORT
# ========================================

@login_required
@verified_email_required
@role_required('EG', 'OM', 'PM')
def export_weekly_cost_pdf(request, project_id):
    """
    Export weekly cost reports to PDF with charts and tables
    """
    try:
        project = get_object_or_404(ProjectProfile, id=project_id)
        user_profile = request.user.userprofile

        # Check permissions
        if user_profile.role == 'PM' and project.project_manager != user_profile:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        # Get query params for date filtering
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        # Get POST body for include options and chart data
        if request.method == 'POST':
            body = json.loads(request.body)
            include_options = body.get('includeOptions', {})
            chart_data = body.get('chartData', {})
        else:
            include_options = {}
            chart_data = {}

        # Query weekly reports
        reports = WeeklyCostReport.objects.filter(project=project)
        if start_date and end_date:
            reports = reports.filter(
                period_start__gte=start_date,
                period_end__lte=end_date
            )

        # Aggregate data
        monthly_summary = aggregate_monthly_data(reports)
        totals = calculate_totals(reports)

        # Prepare context for PDF template
        context = {
            'project': project,
            'start_date': start_date or 'All',
            'end_date': end_date or 'All',
            'generated_date': timezone.now().strftime('%B %d, %Y %I:%M %p'),
            'weekly_reports': reports,
            'monthly_summary': monthly_summary,
            'totals': totals,
            'include_project_header': include_options.get('project_header', True),
            'include_weekly_table': include_options.get('weekly_table', True),
            'include_monthly_table': include_options.get('monthly_table', True),
            'include_weekly_chart': include_options.get('weekly_chart', True),
            'include_monthly_chart': include_options.get('monthly_chart', True),
            'include_totals': include_options.get('totals', True),
            'include_category_breakdown': include_options.get('category_breakdown', True),
            'weekly_chart_image': chart_data.get('weeklyChart'),
            'monthly_chart_image': chart_data.get('monthlyChart'),
        }

        # Render HTML template
        html_string = render_to_string(
            'project_profiling/reports/weekly_cost_report_pdf.html',
            context
        )

        # Generate PDF
        html = HTML(string=html_string)
        pdf = html.write_pdf()

        # Create response
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"{project.project_name.replace(' ', '_')}_Cost_Report_{start_date or 'All'}_to_{end_date or 'All'}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ========================================
# EXCEL EXPORT
# ========================================

@login_required
@verified_email_required
@role_required('EG', 'OM', 'PM')
def export_weekly_cost_excel(request, project_id):
    """
    Export weekly cost reports to Excel with multiple sheets
    """
    try:
        project = get_object_or_404(ProjectProfile, id=project_id)
        user_profile = request.user.userprofile

        # Check permissions
        if user_profile.role == 'PM' and project.project_manager != user_profile:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        # Get query params
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        # Get POST body
        if request.method == 'POST':
            body = json.loads(request.body)
            include_options = body.get('includeOptions', {})
            chart_data = body.get('chartData', {})
        else:
            include_options = {}
            chart_data = {}

        # Query data
        reports = WeeklyCostReport.objects.filter(project=project)
        if start_date and end_date:
            reports = reports.filter(
                period_start__gte=start_date,
                period_end__lte=end_date
            )

        monthly_summary = aggregate_monthly_data(reports)
        totals = calculate_totals(reports)

        # Create workbook
        wb = Workbook()

        # Sheet 1: Overview
        ws_overview = wb.active
        ws_overview.title = "Overview"
        create_overview_sheet(ws_overview, project, start_date, end_date, totals, include_options)

        # Sheet 2: Weekly Data
        if include_options.get('weekly_table', True):
            ws_weekly = wb.create_sheet("Weekly Data")
            create_weekly_sheet(ws_weekly, reports, chart_data.get('weeklyChart'), include_options)

        # Sheet 3: Monthly Data
        if include_options.get('monthly_table', True):
            ws_monthly = wb.create_sheet("Monthly Data")
            create_monthly_sheet(ws_monthly, monthly_summary, chart_data.get('monthlyChart'), include_options)

        # Sheet 4: Category Analysis
        if include_options.get('category_breakdown', True):
            ws_category = wb.create_sheet("Category Analysis")
            create_category_sheet(ws_category, reports, totals)

        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        # Create response
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"{project.project_name.replace(' ', '_')}_Cost_Report_{start_date or 'All'}_to_{end_date or 'All'}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ========================================
# EXCEL HELPER FUNCTIONS
# ========================================

def create_overview_sheet(ws, project, start_date, end_date, totals, include_options):
    """Create overview sheet with project details and totals"""
    # Title
    ws['A1'] = 'Weekly Cost Report - Overview'
    ws['A1'].font = Font(size=16, bold=True)
    ws.merge_cells('A1:D1')

    # Project details
    ws['A3'] = 'Project Name:'
    ws['B3'] = project.project_name
    ws['A4'] = 'Project Code:'
    ws['B4'] = project.project_id
    ws['A5'] = 'Report Period:'
    ws['B5'] = f"{start_date or 'All'} to {end_date or 'All'}"
    ws['A6'] = 'Generated:'
    ws['B6'] = timezone.now().strftime('%B %d, %Y %I:%M %p')

    # Make labels bold
    for row in range(3, 7):
        ws[f'A{row}'].font = Font(bold=True)

    # Totals summary
    if include_options.get('totals', True):
        ws['A9'] = 'TOTAL DISBURSEMENT SUMMARY'
        ws['A9'].font = Font(size=14, bold=True)
        ws.merge_cells('A9:B9')

        headers = ['Category', 'Amount (₱)']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(10, col, header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')

        categories = [
            ('GENREQ', totals['genreq']),
            ('MATERIALS', totals['materials']),
            ('LABOR', totals['labor']),
            ('EQUIPMENT', totals['equipment']),
            ('TOTAL', totals['total'])
        ]

        for row, (category, amount) in enumerate(categories, 11):
            ws.cell(row, 1, category)
            ws.cell(row, 2, amount)
            ws.cell(row, 2).number_format = '#,##0.00'
            if category == 'TOTAL':
                ws.cell(row, 1).font = Font(bold=True)
                ws.cell(row, 2).font = Font(bold=True)
                ws.cell(row, 1).fill = PatternFill(start_color='FFF59D', end_color='FFF59D', fill_type='solid')
                ws.cell(row, 2).fill = PatternFill(start_color='FFF59D', end_color='FFF59D', fill_type='solid')

    # Auto-fit columns
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 30


def create_weekly_sheet(ws, reports, chart_image, include_options):
    """Create weekly data sheet"""
    # Title
    ws['A1'] = 'Week-to-Week Summary'
    ws['A1'].font = Font(size=14, bold=True)

    # Headers
    headers = ['DATE', 'PERIOD', 'GENREQ', 'MATERIALS', 'LABOR', 'EQUIPMENT', 'TOTAL']
    header_fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')
    header_font = Font(bold=True)

    for col, header in enumerate(headers, 1):
        cell = ws.cell(3, col, header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')

    # Data rows
    row = 4
    for report in reports:
        ws.cell(row, 1, report.report_date.strftime('%Y-%m-%d'))
        ws.cell(row, 2, f"{report.period_start.strftime('%Y-%m-%d')} - {report.period_end.strftime('%Y-%m-%d')}")
        ws.cell(row, 3, float(report.genreq_amount))
        ws.cell(row, 4, float(report.materials_amount))
        ws.cell(row, 5, float(report.labor_amount))
        ws.cell(row, 6, float(report.equipment_amount))
        ws.cell(row, 7, float(report.total_amount))
        row += 1

    # Totals row
    if include_options.get('totals', True):
        totals_fill = PatternFill(start_color='FFF59D', end_color='FFF59D', fill_type='solid')
        totals_font = Font(bold=True)

        ws.cell(row, 1, 'TOTAL DISBURSEMENT')
        ws.cell(row, 1).font = totals_font
        ws.cell(row, 1).fill = totals_fill
        ws.cell(row, 2, '')
        ws.cell(row, 2).fill = totals_fill

        for col in range(3, 8):
            ws.cell(row, col, f'=SUM({get_column_letter(col)}4:{get_column_letter(col)}{row-1})')
            ws.cell(row, col).font = totals_font
            ws.cell(row, col).fill = totals_fill

    # Format currency columns
    for r in range(4, row + 1):
        for col in range(3, 8):
            ws.cell(r, col).number_format = '#,##0.00'

    # Auto-fit columns
    for col in range(1, 8):
        ws.column_dimensions[get_column_letter(col)].width = 15

    # Insert chart image if provided
    if chart_image and include_options.get('weekly_chart', True):
        try:
            insert_chart_image(ws, chart_image, row + 2)
        except:
            pass  # Skip if chart insertion fails


def create_monthly_sheet(ws, monthly_summary, chart_image, include_options):
    """Create monthly data sheet"""
    # Title
    ws['A1'] = 'Month-to-Month Summary'
    ws['A1'].font = Font(size=14, bold=True)

    # Headers
    headers = ['MONTH', 'GENREQ', 'MATERIALS', 'LABOR', 'EQUIPMENT', 'TOTAL']
    header_fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')
    header_font = Font(bold=True)

    for col, header in enumerate(headers, 1):
        cell = ws.cell(3, col, header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')

    # Data rows
    row = 4
    for month_data in monthly_summary:
        ws.cell(row, 1, month_data['month'])
        ws.cell(row, 2, month_data['genreq'])
        ws.cell(row, 3, month_data['materials'])
        ws.cell(row, 4, month_data['labor'])
        ws.cell(row, 5, month_data['equipment'])
        ws.cell(row, 6, month_data['total'])
        row += 1

    # Totals row
    if include_options.get('totals', True):
        totals_fill = PatternFill(start_color='FFF59D', end_color='FFF59D', fill_type='solid')
        totals_font = Font(bold=True)

        ws.cell(row, 1, 'TOTAL DISBURSEMENT')
        ws.cell(row, 1).font = totals_font
        ws.cell(row, 1).fill = totals_fill

        for col in range(2, 7):
            ws.cell(row, col, f'=SUM({get_column_letter(col)}4:{get_column_letter(col)}{row-1})')
            ws.cell(row, col).font = totals_font
            ws.cell(row, col).fill = totals_fill

    # Format currency columns
    for r in range(4, row + 1):
        for col in range(2, 7):
            ws.cell(r, col).number_format = '#,##0.00'

    # Auto-fit columns
    ws.column_dimensions['A'].width = 20
    for col in range(2, 7):
        ws.column_dimensions[get_column_letter(col)].width = 15

    # Insert chart image if provided
    if chart_image and include_options.get('monthly_chart', True):
        try:
            insert_chart_image(ws, chart_image, row + 2)
        except:
            pass


def create_category_sheet(ws, reports, totals):
    """Create category breakdown analysis sheet"""
    # Title
    ws['A1'] = 'Category Breakdown Analysis'
    ws['A1'].font = Font(size=14, bold=True)

    # Category totals
    ws['A3'] = 'Category'
    ws['B3'] = 'Total Amount (₱)'
    ws['C3'] = 'Percentage'

    for col in range(1, 4):
        ws.cell(3, col).font = Font(bold=True)
        ws.cell(3, col).fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')

    categories = [
        ('GENREQ', totals['genreq']),
        ('MATERIALS', totals['materials']),
        ('LABOR', totals['labor']),
        ('EQUIPMENT', totals['equipment'])
    ]

    total_amount = totals['total']
    row = 4
    for category, amount in categories:
        ws.cell(row, 1, category)
        ws.cell(row, 2, amount)
        ws.cell(row, 2).number_format = '#,##0.00'
        percentage = (amount / total_amount * 100) if total_amount > 0 else 0
        ws.cell(row, 3, percentage)
        ws.cell(row, 3).number_format = '0.00%'
        ws.cell(row, 3).value = percentage / 100  # Excel expects decimal for percentage
        row += 1

    # Auto-fit columns
    ws.column_dimensions['A'].width = 15
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 15


def insert_chart_image(ws, base64_image, start_row):
    """Insert chart image into Excel worksheet"""
    try:
        # Decode base64 image
        image_data = base64.b64decode(base64_image.split(',')[1])
        image = PILImage.open(BytesIO(image_data))

        # Save to temp BytesIO
        img_io = BytesIO()
        image.save(img_io, format='PNG')
        img_io.seek(0)

        # Insert into Excel
        img = XLImage(img_io)
        img.width = 600
        img.height = 400
        ws.add_image(img, f'A{start_row}')

    except Exception as e:
        # Silently fail if image insertion doesn't work
        pass


# ========================================
# DASHBOARD BUDGET SUMMARY API
# ========================================

@login_required
@verified_email_required
def api_dashboard_budget_summary(request):
    """
    API endpoint for dashboard budget chart
    Returns approved budget vs actual disbursement for all projects
    """
    try:
        user_profile = request.user.userprofile

        # Get projects based on role
        if user_profile.role in ['EG', 'OM']:
            projects = ProjectProfile.objects.all()
        elif user_profile.role == 'PM':
            projects = ProjectProfile.objects.filter(project_manager=user_profile)
        else:
            projects = ProjectProfile.objects.none()

        # Prepare data
        project_names = []
        approved_budgets = []
        actual_disbursements = []

        for project in projects:
            project_names.append(project.project_name)

            # Get approved budget (sum of all budget categories)
            from .models import ProjectBudget
            approved_budget = ProjectBudget.objects.filter(
                project_scope__project=project
            ).aggregate(
                total=Sum('planned_amount')
            )['total'] or 0
            approved_budgets.append(float(approved_budget))

            # Get actual disbursement (sum of all weekly reports)
            actual_disbursement = WeeklyCostReport.objects.filter(
                project=project
            ).aggregate(
                total=Sum('total_amount')
            )['total'] or 0
            actual_disbursements.append(float(actual_disbursement))

        return JsonResponse({
            'success': True,
            'project_names': project_names,
            'approved_budgets': approved_budgets,
            'actual_disbursements': actual_disbursements
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
