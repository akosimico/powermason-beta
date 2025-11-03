"""
Progress Excel Exporter
Generates Excel reports for weekly progress in BOQ format
"""

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime
from decimal import Decimal


class ProgressExcelExporter:
    """Export weekly progress reports to Excel in BOQ format"""

    def __init__(self, report):
        """
        Initialize exporter with a WeeklyProgressReport instance

        Args:
            report: WeeklyProgressReport instance
        """
        self.report = report
        self.project = report.project
        self.wb = Workbook()
        self.ws = self.wb.active
        self.ws.title = f"Week {report.week_start_date.strftime('%m-%d')}"

        # Define styles
        self.header_font = Font(name='Arial', size=14, bold=True, color='FFFFFF')
        self.header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')

        self.division_font = Font(name='Arial', size=12, bold=True, color='FFFFFF')
        self.division_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')

        self.task_font = Font(name='Arial', size=11, bold=True)
        self.task_fill = PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')

        self.boq_font = Font(name='Arial', size=10)
        self.bold_font = Font(name='Arial', size=10, bold=True)

        self.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        self.current_row = 1

    def export_weekly_report(self):
        """
        Export weekly progress report to Excel

        Returns:
            Workbook: openpyxl Workbook instance
        """
        self._add_report_header()
        self._add_summary_section()
        self._add_column_headers()
        self._add_boq_items()
        self._add_totals()
        self._format_columns()

        return self.wb

    def _add_report_header(self):
        """Add report header with project info"""
        # Project name
        self.ws[f'A{self.current_row}'] = self.project.project_name
        self.ws[f'A{self.current_row}'].font = Font(name='Arial', size=16, bold=True)
        self.current_row += 1

        # Report title
        self.ws[f'A{self.current_row}'] = f"Weekly Progress Report #{self.report.report_number}"
        self.ws[f'A{self.current_row}'].font = Font(name='Arial', size=14, bold=True)
        self.current_row += 1

        # Week info
        week_text = f"Week: {self.report.week_start_date.strftime('%B %d, %Y')} - {self.report.week_end_date.strftime('%B %d, %Y')}"
        self.ws[f'A{self.current_row}'] = week_text
        self.ws[f'A{self.current_row}'].font = Font(name='Arial', size=11)
        self.current_row += 1

        # Status
        status_text = f"Status: {self.report.get_status_display()}"
        self.ws[f'A{self.current_row}'] = status_text
        self.ws[f'A{self.current_row}'].font = Font(name='Arial', size=11, bold=True)
        if self.report.status == 'A':
            self.ws[f'A{self.current_row}'].font = Font(name='Arial', size=11, bold=True, color='008000')
        elif self.report.status == 'R':
            self.ws[f'A{self.current_row}'].font = Font(name='Arial', size=11, bold=True, color='FF0000')
        self.current_row += 2

    def _add_summary_section(self):
        """Add summary statistics"""
        # Summary header
        self.ws[f'A{self.current_row}'] = "SUMMARY"
        self.ws[f'A{self.current_row}'].font = Font(name='Arial', size=12, bold=True)
        self.current_row += 1

        # Summary data
        summary_data = [
            ('Period Progress:', f"{self.report.total_period_percent:.2f}%"),
            ('Period Amount:', f"₱{self.report.total_period_amount:,.2f}"),
            ('Cumulative Progress:', f"{self.report.cumulative_project_percent:.2f}%"),
            ('Cumulative Amount:', f"₱{self.report.cumulative_project_amount:,.2f}"),
        ]

        for label, value in summary_data:
            self.ws[f'A{self.current_row}'] = label
            self.ws[f'A{self.current_row}'].font = self.bold_font
            self.ws[f'B{self.current_row}'] = value
            self.ws[f'B{self.current_row}'].font = self.boq_font
            self.current_row += 1

        self.current_row += 1

        # Submission info
        self.ws[f'A{self.current_row}'] = f"Submitted by: {self.report.submitted_by.get_full_name()}"
        self.current_row += 1
        self.ws[f'A{self.current_row}'] = f"Submitted on: {self.report.submitted_at.strftime('%B %d, %Y %I:%M %p')}"
        self.current_row += 1

        if self.report.status == 'A':
            self.ws[f'A{self.current_row}'] = f"Approved by: {self.report.reviewed_by.get_full_name()}"
            self.current_row += 1
            self.ws[f'A{self.current_row}'] = f"Approved on: {self.report.reviewed_at.strftime('%B %d, %Y %I:%M %p')}"
            self.current_row += 1

        self.current_row += 2

    def _add_column_headers(self):
        """Add column headers for BOQ items"""
        headers = [
            'BOQ Code',
            'Description',
            'Division',
            'Task',
            'Qty',
            'UOM',
            'Approved Amount',
            'Previous %',
            'Current %',
            'Period %',
            'Period Amount',
            'Remarks'
        ]

        for col_num, header in enumerate(headers, start=1):
            cell = self.ws.cell(row=self.current_row, column=col_num)
            cell.value = header
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.border = self.border

        self.current_row += 1

    def _add_boq_items(self):
        """Add BOQ items grouped by division"""
        from project_profiling.models import BOQItemProgress

        # Get all BOQ items for this report
        boq_items = BOQItemProgress.objects.filter(
            weekly_report=self.report
        ).select_related('project_task').order_by('division', 'task_group', 'boq_item_code')

        # Group by division
        current_division = None

        for item in boq_items:
            # Add division header if changed
            if current_division != item.division:
                if current_division is not None:
                    self.current_row += 1  # Blank row between divisions

                # Division header
                cell = self.ws.cell(row=self.current_row, column=1)
                cell.value = item.division
                cell.font = self.division_font
                cell.fill = self.division_fill
                cell.alignment = Alignment(horizontal='left', vertical='center')

                # Merge across all columns
                self.ws.merge_cells(
                    start_row=self.current_row,
                    start_column=1,
                    end_row=self.current_row,
                    end_column=12
                )

                for col in range(1, 13):
                    self.ws.cell(row=self.current_row, column=col).border = self.border

                self.current_row += 1
                current_division = item.division

            # BOQ item row
            row_data = [
                item.boq_item_code,
                item.description,
                item.division,
                item.task_group,
                float(item.quantity) if item.quantity else 0,
                item.unit_of_measurement,
                float(item.approved_contract_amount),
                float(item.previous_cumulative_percent),
                float(item.cumulative_percent),
                float(item.period_progress_percent),
                float(item.period_progress_amount),
                item.remarks or ''
            ]

            for col_num, value in enumerate(row_data, start=1):
                cell = self.ws.cell(row=self.current_row, column=col_num)
                cell.value = value
                cell.font = self.boq_font
                cell.border = self.border

                # Format numbers
                if col_num in [5]:  # Quantity
                    cell.number_format = '#,##0.00'
                elif col_num in [7, 11]:  # Amounts
                    cell.number_format = '₱#,##0.00'
                elif col_num in [8, 9, 10]:  # Percentages
                    cell.number_format = '0.00"%"'
                    # Color code period progress
                    if col_num == 10:
                        if value > 0:
                            cell.font = Font(name='Arial', size=10, color='008000')  # Green
                        elif value < 0:
                            cell.font = Font(name='Arial', size=10, color='FF0000')  # Red

                # Alignment
                if col_num in [1, 3, 4, 6, 12]:  # Text columns
                    cell.alignment = Alignment(horizontal='left', vertical='center')
                else:  # Number columns
                    cell.alignment = Alignment(horizontal='right', vertical='center')

            # Highlight if progress decreased
            if item.progress_decreased:
                for col in range(1, 13):
                    self.ws.cell(row=self.current_row, column=col).fill = PatternFill(
                        start_color='FFF2CC', end_color='FFF2CC', fill_type='solid'
                    )

            self.current_row += 1

    def _add_totals(self):
        """Add totals row"""
        self.current_row += 1

        # Totals label
        cell = self.ws.cell(row=self.current_row, column=1)
        cell.value = "TOTALS"
        cell.font = Font(name='Arial', size=11, bold=True)
        cell.fill = PatternFill(start_color='E7E6E6', end_color='E7E6E6', fill_type='solid')
        cell.border = self.border

        # Merge first few columns
        self.ws.merge_cells(
            start_row=self.current_row,
            start_column=1,
            end_row=self.current_row,
            end_column=6
        )

        for col in range(1, 7):
            self.ws.cell(row=self.current_row, column=col).border = self.border
            self.ws.cell(row=self.current_row, column=col).fill = PatternFill(
                start_color='E7E6E6', end_color='E7E6E6', fill_type='solid'
            )

        # Period progress %
        cell = self.ws.cell(row=self.current_row, column=10)
        cell.value = float(self.report.total_period_percent)
        cell.number_format = '0.00"%"'
        cell.font = Font(name='Arial', size=11, bold=True)
        cell.fill = PatternFill(start_color='E7E6E6', end_color='E7E6E6', fill_type='solid')
        cell.border = self.border
        cell.alignment = Alignment(horizontal='right', vertical='center')

        # Period amount
        cell = self.ws.cell(row=self.current_row, column=11)
        cell.value = float(self.report.total_period_amount)
        cell.number_format = '₱#,##0.00'
        cell.font = Font(name='Arial', size=11, bold=True)
        cell.fill = PatternFill(start_color='E7E6E6', end_color='E7E6E6', fill_type='solid')
        cell.border = self.border
        cell.alignment = Alignment(horizontal='right', vertical='center')

        # Empty cells
        for col in [7, 8, 9, 12]:
            cell = self.ws.cell(row=self.current_row, column=col)
            cell.fill = PatternFill(start_color='E7E6E6', end_color='E7E6E6', fill_type='solid')
            cell.border = self.border

    def _format_columns(self):
        """Set column widths"""
        column_widths = {
            'A': 12,  # BOQ Code
            'B': 40,  # Description
            'C': 25,  # Division
            'D': 25,  # Task
            'E': 10,  # Qty
            'F': 8,   # UOM
            'G': 15,  # Approved Amount
            'H': 12,  # Previous %
            'I': 12,  # Current %
            'J': 12,  # Period %
            'K': 15,  # Period Amount
            'L': 30,  # Remarks
        }

        for col, width in column_widths.items():
            self.ws.column_dimensions[col].width = width


def export_weekly_report_to_excel(report):
    """
    Export a weekly progress report to Excel

    Args:
        report: WeeklyProgressReport instance

    Returns:
        Workbook: openpyxl Workbook instance ready to save
    """
    exporter = ProgressExcelExporter(report)
    return exporter.export_weekly_report()


def export_multiple_reports_to_excel(reports):
    """
    Export multiple weekly progress reports to a single Excel file
    with each report in a separate sheet

    Args:
        reports: QuerySet or list of WeeklyProgressReport instances

    Returns:
        Workbook: openpyxl Workbook instance with multiple sheets
    """
    if not reports:
        # Return empty workbook with message
        wb = Workbook()
        ws = wb.active
        ws.title = "No Reports"
        ws['A1'] = "No reports to export"
        return wb

    # Create first report
    first_report = reports[0]
    exporter = ProgressExcelExporter(first_report)
    wb = exporter.export_weekly_report()

    # Add remaining reports as new sheets
    for report in reports[1:]:
        # Create new exporter for each report
        exporter = ProgressExcelExporter(report)
        exporter.wb = wb
        exporter.ws = wb.create_sheet(title=f"Week {report.week_start_date.strftime('%m-%d')}")
        exporter.export_weekly_report()

    return wb
