"""
Task Creator Module
Creates ProjectTask instances from approved schedule data
Auto-links BOQ items to tasks for progress tracking
"""

from decimal import Decimal
from datetime import datetime
from django.db import transaction
from .models import ProjectTask, ProjectScope
import logging
import re

logger = logging.getLogger(__name__)


class TaskCreator:
    """Create tasks from parsed schedule data"""

    def __init__(self, schedule):
        """
        Initialize creator with ProjectSchedule instance

        Args:
            schedule: ProjectSchedule instance with parsed_data
        """
        self.schedule = schedule
        self.project = schedule.project
        self.uploaded_by = schedule.uploaded_by
        self.created_tasks = []
        self.errors = []
        self.boq_items = self._get_boq_items()

    @transaction.atomic
    def create_tasks(self):
        """
        Create all tasks from schedule data

        Returns:
            dict: Creation results with success flag and created task count
        """
        if not self.schedule.parsed_data or not self.schedule.parsed_data.get('scopes'):
            return {
                'success': False,
                'error': 'No parsed data available in schedule',
                'created_count': 0,
                'tasks': []
            }

        scopes_data = self.schedule.parsed_data.get('scopes', [])

        for scope_data in scopes_data:
            try:
                self._create_tasks_for_scope(scope_data)
            except Exception as e:
                logger.error(f"Error creating tasks for scope {scope_data.get('scope_name')}: {str(e)}")
                self.errors.append(f"Scope {scope_data.get('scope_name')}: {str(e)}")

        if self.errors:
            # Rollback transaction if any errors
            transaction.set_rollback(True)
            return {
                'success': False,
                'error': '; '.join(self.errors),
                'created_count': 0,
                'tasks': []
            }

        return {
            'success': True,
            'created_count': len(self.created_tasks),
            'tasks': self.created_tasks
        }

    def _create_tasks_for_scope(self, scope_data):
        """Create tasks for a single scope"""
        scope_id = scope_data.get('scope_id')
        scope_name = scope_data.get('scope_name')
        tasks_data = scope_data.get('tasks', [])

        if not tasks_data:
            logger.warning(f"No tasks found for scope {scope_name}")
            return

        # Get scope instance
        try:
            scope = ProjectScope.objects.get(id=scope_id, project=self.project)
        except ProjectScope.DoesNotExist:
            raise ValueError(f"Scope '{scope_name}' not found in project")

        # Calculate task weights (equal distribution within scope)
        task_count = len(tasks_data)
        task_weight = Decimal('100.00') / task_count if task_count > 0 else Decimal('0')

        # Create tasks
        for task_data in tasks_data:
            task = self._create_single_task(scope, task_data, task_weight)
            if task:
                self.created_tasks.append(task)

    def _create_single_task(self, scope, task_data, weight):
        """
        Create a single ProjectTask instance

        Args:
            scope: ProjectScope instance
            task_data: Dict with task information
            weight: Calculated weight for this task

        Returns:
            ProjectTask: Created task instance
        """
        try:
            # Parse ISO format date strings back to date objects
            start_date = task_data['start_date']
            end_date = task_data['end_date']

            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date).date()
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date).date()

            task = ProjectTask.objects.create(
                project=self.project,
                scope=scope,
                task_name=task_data['task_name'],
                description=f"Item {task_data.get('item_number', 'N/A')}",
                start_date=start_date,
                end_date=end_date,
                duration_days=task_data['duration_days'],
                manhours=task_data['manhours'],
                weight=weight,
                progress=Decimal('0'),
                status='PL',  # Planned
                assigned_to=self.uploaded_by,  # Assign to PM who uploaded schedule
                is_completed=False,
                is_archived=False
            )

            # Auto-link BOQ items to this task
            linked_boq_codes = self._link_boq_items_to_task(task, scope.name)
            if linked_boq_codes:
                task.boq_item_codes = linked_boq_codes
                task.update_approved_amount()  # Calculate approved amount from linked items
                logger.info(f"Linked {len(linked_boq_codes)} BOQ items to task: {task.task_name}")

            logger.info(f"Created task: {task.task_name} in scope {scope.name}")
            return task

        except Exception as e:
            logger.error(f"Error creating task {task_data.get('task_name')}: {str(e)}")
            raise

    def _get_boq_items(self):
        """
        Get BOQ items from project.
        Returns list of BOQ items with their codes, descriptions, and divisions.
        """
        if not self.project.boq_items:
            return []

        boq_items = []
        for item in self.project.boq_items:
            # Only get level 2 items (actual materials/activities with quantities)
            level = item.get('level', 0)
            if level == 2:  # Level 2 items like 1.1.1, 7.1.3
                boq_items.append({
                    'code': item.get('code', ''),
                    'description': item.get('description', ''),
                    'division': item.get('division', ''),
                    'task_group': item.get('task', ''),
                    'amount': item.get('amount', 0),
                    'quantity': item.get('quantity', 0),
                    'uom': item.get('uom', '')
                })

        return boq_items

    def _link_boq_items_to_task(self, task, scope_name):
        """
        Auto-link BOQ items to a task based on matching criteria.

        Matching logic:
        1. Division name matches scope name
        2. Task group name matches or is similar to task name
        3. Keyword matching in descriptions

        Args:
            task: ProjectTask instance
            scope_name: Name of the scope/division

        Returns:
            list: List of BOQ item codes linked to this task
        """
        if not self.boq_items:
            return []

        linked_codes = []

        # Normalize scope name for matching
        normalized_scope = self._normalize_text(scope_name)

        for boq_item in self.boq_items:
            # Check if division matches scope
            normalized_division = self._normalize_text(boq_item['division'])

            if normalized_scope in normalized_division or normalized_division in normalized_scope:
                # Division matches, now check task name similarity
                if self._is_task_match(task.task_name, boq_item['task_group'], boq_item['description']):
                    linked_codes.append(boq_item['code'])

        return linked_codes

    def _is_task_match(self, task_name, boq_task_group, boq_description):
        """
        Check if BOQ item matches the task based on name and description.

        Args:
            task_name: Name of the ProjectTask
            boq_task_group: Task group from BOQ (e.g., "Site Mobilization")
            boq_description: Description of BOQ item

        Returns:
            bool: True if there's a match
        """
        # Normalize all strings
        norm_task = self._normalize_text(task_name)
        norm_group = self._normalize_text(boq_task_group)
        norm_desc = self._normalize_text(boq_description)

        # Direct match with task group
        if norm_task == norm_group:
            return True

        # Check if task name contains task group or vice versa
        if norm_task in norm_group or norm_group in norm_task:
            return True

        # Extract keywords from task name and check against description
        task_keywords = self._extract_keywords(norm_task)
        desc_keywords = self._extract_keywords(norm_desc)

        # If 2 or more keywords match, consider it a match
        matching_keywords = task_keywords.intersection(desc_keywords)
        if len(matching_keywords) >= 2:
            return True

        return False

    def _normalize_text(self, text):
        """
        Normalize text for comparison.
        Converts to lowercase and removes special characters.
        """
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove special characters and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _extract_keywords(self, text):
        """
        Extract meaningful keywords from text.
        Removes common stop words.
        """
        stop_words = {
            'the', 'and', 'or', 'of', 'to', 'in', 'for', 'a', 'an',
            'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'with', 'at', 'by', 'from', 'as', 'all', 'any',
            'complete', 'supply', 'delivery', 'installation'
        }

        # Split into words
        words = text.split()

        # Filter out stop words and short words
        keywords = {w for w in words if len(w) > 2 and w not in stop_words}

        return keywords


def create_tasks_from_schedule(schedule):
    """
    Main function to create tasks from an approved schedule

    Args:
        schedule: ProjectSchedule instance

    Returns:
        dict: Creation results
    """
    creator = TaskCreator(schedule)
    return creator.create_tasks()


def get_schedule_summary(schedule):
    """
    Generate summary statistics for a schedule

    Args:
        schedule: ProjectSchedule instance with parsed_data

    Returns:
        dict: Summary statistics
    """
    if not schedule.parsed_data or not schedule.parsed_data.get('scopes'):
        return {
            'total_tasks': 0,
            'scopes_count': 0,
            'date_range': None,
            'total_manhours': 0
        }

    scopes_data = schedule.parsed_data.get('scopes', [])
    total_tasks = 0
    total_manhours = Decimal('0')
    earliest_date = None
    latest_date = None

    for scope_data in scopes_data:
        tasks = scope_data.get('tasks', [])
        total_tasks += len(tasks)

        for task in tasks:
            # Sum manhours
            if task.get('manhours'):
                total_manhours += Decimal(str(task['manhours']))

            # Track date range - parse ISO format strings to date objects
            start_date = task.get('start_date')
            end_date = task.get('end_date')

            # Convert ISO strings to date objects
            if start_date:
                if isinstance(start_date, str):
                    start_date = datetime.fromisoformat(start_date).date()
                if earliest_date is None or start_date < earliest_date:
                    earliest_date = start_date
            if end_date:
                if isinstance(end_date, str):
                    end_date = datetime.fromisoformat(end_date).date()
                if latest_date is None or end_date > latest_date:
                    latest_date = end_date

    # Calculate total duration
    total_duration = 0
    if earliest_date and latest_date:
        total_duration = (latest_date - earliest_date).days + 1

    return {
        'total_tasks': total_tasks,
        'scopes_count': len(scopes_data),
        'earliest_date': earliest_date,  # Return as date object, not ISO string
        'latest_date': latest_date,      # Return as date object, not ISO string
        'total_duration': total_duration,
        'total_manhours': float(total_manhours)
    }
