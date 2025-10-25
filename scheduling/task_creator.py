"""
Task Creator Module
Creates ProjectTask instances from approved schedule data
"""

from decimal import Decimal
from datetime import datetime
from django.db import transaction
from .models import ProjectTask, ProjectScope
import logging

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

            logger.info(f"Created task: {task.task_name} in scope {scope.name}")
            return task

        except Exception as e:
            logger.error(f"Error creating task {task_data.get('task_name')}: {str(e)}")
            raise


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
