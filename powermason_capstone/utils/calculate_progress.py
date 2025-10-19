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
