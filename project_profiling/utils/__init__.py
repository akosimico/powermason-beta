# Utils package for project_profiling app

# Import all utility functions to make them available
from .rfs_generator import generate_rfs_from_boq, generate_rfs_buffer_from_boq, get_rfs_download_info
from .quotation_processor import extract_total_from_excel, create_tasks_from_approved_quotation

# Import the recalc_project_progress function from the parent utils module
try:
    from ..utils import recalc_project_progress
except ImportError:
    # If the function doesn't exist, create a placeholder
    def recalc_project_progress(*args, **kwargs):
        """Placeholder function for recalc_project_progress"""
        pass
