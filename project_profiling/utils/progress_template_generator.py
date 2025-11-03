"""
Progress Report Template Generator
Generates blank weekly progress report templates based on approved project schedule and BOQ
"""

from decimal import Decimal
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ProgressTemplateGenerator:
    """Generate weekly progress report template with pre-filled BOQ items"""

    def __init__(self, project):
        """
        Initialize generator with project instance

        Args:
            project: ProjectProfile instance with approved schedule and BOQ
        """
        self.project = project
        self.approved_quotation = self._get_approved_quotation()

    def _get_approved_quotation(self):
        """Get approved supplier quotation for this project"""
        from project_profiling.models import SupplierQuotation

        return SupplierQuotation.objects.filter(
            project_id=self.project.id,
            project_type='profile',
            status='APPROVED'
        ).first()

    def generate_template_for_week(self, week_start_date, week_end_date):
        """
        Generate progress report template for a specific week.
        Now simplified: Shows ALL BOQ items grouped by division.
        PM decides which items to report on.

        Args:
            week_start_date: Date object for start of week
            week_end_date: Date object for end of week

        Returns:
            dict: Template data with ALL BOQ items from project
        """
        logger.info(f"[TEMPLATE] Generating template for project ID {self.project.id}: {self.project.project_name}")
        logger.info(f"[TEMPLATE] Week: {week_start_date} to {week_end_date}")

        # Build template structure
        template = {
            'project_id': self.project.id,
            'project_code': self.project.project_id,  # GC-057 format
            'project_name': self.project.project_name,
            'week_start_date': week_start_date.isoformat(),
            'week_end_date': week_end_date.isoformat(),
            'approved_budget': float(self.project.approved_budget) if self.project.approved_budget else 0,
            'divisions': []
        }

        # Get ALL BOQ items from project, grouped by division
        if not self.project.boq_items:
            logger.warning(f"[TEMPLATE] No BOQ items found for project {self.project.id}")
            return template

        # Group BOQ items by division
        divisions = {}

        for boq_item in self.project.boq_items:
            # Only include level 2 items (actual work items, not headers)
            level = boq_item.get('level', 0)
            if level != 2:
                continue

            division_name = boq_item.get('division', 'Other')

            if division_name not in divisions:
                divisions[division_name] = {
                    'name': division_name,
                    'boq_items': []
                }

            # Get previous progress for this BOQ item
            from project_profiling.models import BOQItemProgress

            boq_code = boq_item.get('code', '')
            previous_progress = BOQItemProgress.objects.filter(
                project=self.project,
                boq_item_code=boq_code,
                status='A'  # Only approved
            ).order_by('-report_date').first()

            item_data = {
                'code': boq_code,
                'description': boq_item.get('description', ''),
                'quantity': boq_item.get('quantity', 0),
                'uom': boq_item.get('uom', ''),
                'unit_price': boq_item.get('unit_price', 0),
                'approved_amount': boq_item.get('amount', 0),
                'previous_cumulative_percent': float(previous_progress.cumulative_percent) if previous_progress else 0,
                'previous_cumulative_amount': float(previous_progress.cumulative_amount) if previous_progress else 0,
            }

            divisions[division_name]['boq_items'].append(item_data)

        template['divisions'] = list(divisions.values())

        # Count total items
        total_items = sum(len(div['boq_items']) for div in template['divisions'])
        logger.info(f"[TEMPLATE] Generated template with {len(divisions)} divisions and {total_items} BOQ items")

        return template

    def _get_boq_items_for_task(self, task):
        """
        Get BOQ items linked to a task with previous progress data.

        Args:
            task: ProjectTask instance

        Returns:
            list: List of BOQ item dictionaries
        """
        from project_profiling.models import BOQItemProgress

        logger.info(f"[BOQ ITEMS DEBUG] Getting BOQ items for task ID {task.id}: '{task.task_name}'")
        logger.info(f"[BOQ ITEMS DEBUG] Task.boq_item_codes = {task.boq_item_codes}")
        logger.info(f"[BOQ ITEMS DEBUG] Type: {type(task.boq_item_codes)}, Length: {len(task.boq_item_codes) if task.boq_item_codes else 0}")

        if not task.boq_item_codes:
            logger.warning(f"[BOQ ITEMS DEBUG] Task {task.id} '{task.task_name}' has NO boq_item_codes - returning empty list")
            return []

        logger.info(f"[BOQ ITEMS DEBUG] Task {task.id} has {len(task.boq_item_codes)} BOQ codes: {task.boq_item_codes}")

        boq_items_data = []

        for boq_code in task.boq_item_codes:
            # Get BOQ item details from project.boq_items
            boq_item = self._find_boq_item_by_code(boq_code)

            if not boq_item:
                continue

            # Get previous approved progress for this item
            previous_progress = BOQItemProgress.objects.filter(
                project=self.project,
                boq_item_code=boq_code,
                status='A'  # Only approved
            ).order_by('-report_date').first()

            item_data = {
                'code': boq_code,
                'description': boq_item.get('description', ''),
                'quantity': boq_item.get('quantity', 0),
                'uom': boq_item.get('uom', ''),
                'approved_amount': boq_item.get('amount', 0),
                'previous_cumulative_percent': float(previous_progress.cumulative_percent) if previous_progress else 0,
                'previous_cumulative_amount': float(previous_progress.cumulative_amount) if previous_progress else 0,
                'scheduled_start_date': task.start_date.isoformat(),
                'scheduled_end_date': task.end_date.isoformat()
            }

            boq_items_data.append(item_data)

        logger.info(f"[BOQ ITEMS DEBUG] Returning {len(boq_items_data)} BOQ items for task {task.id}")
        return boq_items_data

    def _find_boq_item_by_code(self, boq_code):
        """
        Find BOQ item in project.boq_items by code

        Args:
            boq_code: BOQ item code (e.g., "1.1.1")

        Returns:
            dict: BOQ item data or None
        """
        if not self.project.boq_items:
            return None

        for item in self.project.boq_items:
            if item.get('code') == boq_code:
                return item

        return None

    def get_weekly_schedule(self, start_date=None, num_weeks=12):
        """
        Get weekly schedule for progress reporting.

        Args:
            start_date: Starting date (defaults to project start)
            num_weeks: Number of weeks to generate

        Returns:
            list: List of week dictionaries with dates and tasks
        """
        from scheduling.models import ProjectTask

        # Get project start date
        if not start_date:
            first_task = ProjectTask.objects.filter(
                project=self.project
            ).order_by('start_date').first()

            if first_task:
                start_date = first_task.start_date
            else:
                start_date = datetime.now().date()

        weeks = []
        current_date = start_date

        for week_num in range(num_weeks):
            week_start = current_date
            week_end = current_date + timedelta(days=6)

            # Get tasks scheduled for this week
            tasks_count = ProjectTask.objects.filter(
                project=self.project,
                start_date__lte=week_end,
                end_date__gte=week_start,
                is_archived=False
            ).count()

            weeks.append({
                'week_number': week_num + 1,
                'start_date': week_start.isoformat(),
                'end_date': week_end.isoformat(),
                'tasks_count': tasks_count
            })

            current_date = week_end + timedelta(days=1)  # Move to next week

        return weeks


def generate_progress_template(project, week_start_date, week_end_date):
    """
    Main function to generate progress report template.

    Args:
        project: ProjectProfile instance
        week_start_date: Date object for week start
        week_end_date: Date object for week end

    Returns:
        dict: Template data
    """
    generator = ProgressTemplateGenerator(project)
    return generator.generate_template_for_week(week_start_date, week_end_date)


def get_project_weekly_schedule(project, start_date=None, num_weeks=12):
    """
    Get weekly reporting schedule for a project.

    Args:
        project: ProjectProfile instance
        start_date: Optional start date
        num_weeks: Number of weeks to generate

    Returns:
        list: Weekly schedule data
    """
    generator = ProgressTemplateGenerator(project)
    return generator.get_weekly_schedule(start_date, num_weeks)
