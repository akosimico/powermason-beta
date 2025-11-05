from datetime import date, datetime

def calculate_progress(start_date, end_date, today=None):
    """
    Calculate smooth timeline progress (0–100%) between start_date and end_date.
    Uses partial days for better accuracy.
    """
    if not start_date or not end_date or start_date >= end_date:
        return 0.0

    # Allow testing or custom 'today'
    if today is None:
        today = datetime.now().date()

    total_days = (end_date - start_date).days
    if total_days <= 0:
        return 0.0

    elapsed_days = (today - start_date).days

    # Smooth percentage
    progress = (elapsed_days / total_days) * 100

    # Clamp between 0 and 100
    return round(max(0, min(progress, 100)), 2)


def calculate_schedule_performance(actual_progress, start_date, target_date, today=None):
    """
    Calculate Schedule Performance Index (SPI) to determine if project is on track, delayed, or ahead.

    Args:
        actual_progress: Float - Actual work completion percentage (0-100)
        start_date: Date - Project start date
        target_date: Date - Project target completion date
        today: Date (optional) - Current date for testing

    Returns:
        dict with:
            - spi: Schedule Performance Index (actual / expected)
            - status: 'on_track', 'at_risk', 'delayed', or 'ahead'
            - expected_progress: What percentage should be completed by now
            - variance: Difference between actual and expected (positive = ahead, negative = behind)
            - display_progress: The progress value to show in UI
    """
    if today is None:
        today = datetime.now().date()

    # If no target date is set, use actual progress only
    if not target_date or not start_date:
        return {
            'spi': 1.0,
            'status': 'unknown',
            'expected_progress': actual_progress,
            'variance': 0.0,
            'display_progress': actual_progress,
            'use_schedule_tracking': False
        }

    # Calculate expected progress based on timeline
    expected_progress = calculate_progress(start_date, target_date, today)

    # Handle edge cases
    if expected_progress == 0:
        # Project hasn't started yet according to timeline
        return {
            'spi': 1.0,
            'status': 'not_started',
            'expected_progress': 0.0,
            'variance': actual_progress,
            'display_progress': actual_progress,
            'use_schedule_tracking': True
        }

    if actual_progress == 0:
        # No work completed but time is passing
        return {
            'spi': 0.0,
            'status': 'delayed',
            'expected_progress': expected_progress,
            'variance': -expected_progress,
            'display_progress': 0.0,
            'use_schedule_tracking': True
        }

    # Calculate Schedule Performance Index
    spi = actual_progress / expected_progress
    variance = actual_progress - expected_progress

    # Determine status based on SPI
    if spi >= 1.05:
        status = 'ahead'
    elif spi >= 0.95:
        status = 'on_track'
    elif spi >= 0.80:
        status = 'at_risk'
    else:
        status = 'delayed'

    return {
        'spi': round(spi, 2),
        'status': status,
        'expected_progress': round(expected_progress, 2),
        'variance': round(variance, 2),
        'display_progress': round(actual_progress, 2),
        'use_schedule_tracking': True
    }
def calculate_schedule_performance(actual_progress, start_date, target_date, today=None, has_approved_report=True):
    """
    Calculate Schedule Performance Index (SPI) with timeline tracking and
    fallback for missing approved progress reports.
    """
    if today is None:
        today = datetime.now().date()

    # --- If no dates, disable schedule tracking ---
    if not target_date or not start_date:
        return {
            'spi': 1.0,
            'status': 'unknown',
            'expected_progress': actual_progress,
            'variance': 0.0,
            'display_progress': actual_progress,
            'use_schedule_tracking': False
        }

    # --- Compute expected progress (timeline progress) ---
    expected_progress = calculate_progress(start_date, target_date, today)

    # --- Case 1: No approved reports ---
    if not has_approved_report:
        return {
            'spi': 0.0,
            'status': 'delayed' if expected_progress > 0 else 'not_started',
            'expected_progress': round(expected_progress, 2),
            'variance': round(0 - expected_progress, 2),  # -expected_progress
            'display_progress': 0.0,
            'use_schedule_tracking': True
        }

    # --- Case 2: Approved reports exist (normal flow) ---
    if expected_progress == 0:
        return {
            'spi': 1.0,
            'status': 'not_started',
            'expected_progress': 0.0,
            'variance': actual_progress,
            'display_progress': actual_progress,
            'use_schedule_tracking': True
        }

    if actual_progress == 0:
        return {
            'spi': 0.0,
            'status': 'delayed',
            'expected_progress': expected_progress,
            'variance': -expected_progress,
            'display_progress': 0.0,
            'use_schedule_tracking': True
        }

    spi = actual_progress / expected_progress
    variance = actual_progress - expected_progress

    if spi >= 1.05:
        status = 'ahead'
    elif spi >= 0.95:
        status = 'on_track'
    elif spi >= 0.80:
        status = 'at_risk'
    else:
        status = 'delayed'

    return {
        'spi': round(spi, 2),
        'status': status,
        'expected_progress': round(expected_progress, 2),
        'variance': round(variance, 2),
        'display_progress': round(actual_progress, 2),
        'use_schedule_tracking': True
    }
