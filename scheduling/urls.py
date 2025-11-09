from django.urls import path
from . import views
from .gantt_views import (
    task_gantt_view, api_gantt_data, api_update_task_dates, three_week_lookahead
)
from .resource_views import (
    task_resource_allocation, api_add_task_material, api_add_task_equipment,
    api_add_task_manpower, api_delete_task_material, api_delete_task_equipment,
    api_delete_task_manpower, api_task_resource_summary
)
from .views import scope_budget_allocation
from .weekly_progress_views import (
    submit_weekly_progress, enter_boq_progress, view_weekly_report,
    list_weekly_reports, review_weekly_reports, approve_weekly_report,
    reject_weekly_report, export_report_excel, export_project_reports_excel,
    export_project_reports_pdf, print_project_reports,
    download_progress_template, upload_progress_excel
)


urlpatterns = [
    # ---------------------------
    # Scheduling / Tasks
    # ---------------------------
    # Session-based task management
    path('<int:project_id>/tasks/', views.task_list, name='task_list'),
    path("<int:project_id>/tasks/add/", views.task_create, name="task_create"),
    path("<int:project_id>/tasks/<int:task_id>/update/", views.task_update, name="task_update"),
    path("<int:project_id>/tasks/<int:task_id>/delete/", views.task_archive, name="task_archive"),
    path("<int:project_id>/tasks/bulk-delete/", views.task_bulk_archive, name="task_bulk_archive"),
    path("<int:project_id>/<int:task_id>/unarchive/", views.task_unarchive, name="task_unarchive"),
    path("<int:project_id>/tasks/unarchive-selected/", views.task_bulk_unarchive, name="task_bulk_unarchive"),
    path("task/<int:task_id>/submit-progress/", views.submit_progress_update, name="submit_progress"),
    
    path('<int:project_id>/create-scope/', views.create_scope_ajax, name='create_scope_ajax'),
    
    # ---------------------------
    # Scope Budget Allocation
    # ---------------------------
    # Session-based scope budget allocation
    path('<int:project_id>/scope-budget/', scope_budget_allocation, name='scope_budget_allocation'),
    
    # ---------------------------
    # Progress Review
    # ---------------------------
    path('progress/review/', views.review_updates, name='review_updates'),
    path('progress/approve/<int:update_id>/', views.approve_update, name='approve_update'),
    path('progress/reject/<int:update_id>/', views.reject_update, name='reject_update'),
    path("progress/history/", views.progress_history, name="progress_history"),

    path("api/pending-count/", views.get_pending_count, name="get_pending_count"),

    # ---------------------------
    # Gantt Chart & Schedule Views
    # ---------------------------
    # Session-based Gantt views
    path('<int:project_id>/gantt/', task_gantt_view, name='task_gantt_view'),
    path('<int:project_id>/lookahead/', three_week_lookahead, name='three_week_lookahead'),

    # API Endpoints
    path('api/projects/<int:project_id>/gantt-data/', api_gantt_data, name='api_gantt_data'),
    path('api/tasks/<int:task_id>/update-dates/', api_update_task_dates, name='api_update_task_dates'),

    # ---------------------------
    # Resource Allocation
    # ---------------------------
    # Session-based resource allocation
    path('<int:project_id>/tasks/<int:task_id>/resources/', task_resource_allocation, name='task_resource_allocation'),

    # Resource API Endpoints
    path('api/tasks/<int:task_id>/resources/summary/', api_task_resource_summary, name='api_task_resource_summary'),
    path('api/tasks/<int:task_id>/materials/add/', api_add_task_material, name='api_add_task_material'),
    path('api/tasks/<int:task_id>/equipment/add/', api_add_task_equipment, name='api_add_task_equipment'),
    path('api/tasks/<int:task_id>/manpower/add/', api_add_task_manpower, name='api_add_task_manpower'),
    path('api/materials/<int:allocation_id>/delete/', api_delete_task_material, name='api_delete_task_material'),
    path('api/equipment/<int:allocation_id>/delete/', api_delete_task_equipment, name='api_delete_task_equipment'),
    path('api/manpower/<int:allocation_id>/delete/', api_delete_task_manpower, name='api_delete_task_manpower'),

    # ---------------------------
    # Schedule Management
    # ---------------------------
    # Template Generation & Upload
    path('<int:project_id>/schedule/generate/', views.generate_schedule_template, name='generate_schedule_template'),
    path('<int:project_id>/schedule/upload/', views.upload_project_schedule, name='upload_project_schedule'),
    path('schedule/<int:schedule_id>/detail/', views.schedule_detail, name='schedule_detail'),
    path('schedule/<int:schedule_id>/submit/', views.submit_schedule_for_approval, name='submit_schedule_for_approval'),

    # Schedule Approval (OM/EG)
    path('schedule/review/', views.review_schedules, name='review_schedules'),
    path('schedule/<int:schedule_id>/review/', views.review_project_schedule, name='review_project_schedule'),
    path('schedule/<int:schedule_id>/approve/', views.approve_schedule, name='approve_schedule'),
    path('schedule/<int:schedule_id>/reject/', views.reject_schedule, name='reject_schedule'),

    # ---------------------------
    # Weekly Progress Reports (BOQ-Based)
    # ---------------------------
    # PM - Submit Weekly Progress
    path('<int:project_id>/progress/weekly/submit/', submit_weekly_progress, name='submit_weekly_progress'),
    path('<int:project_id>/progress/weekly/enter/', enter_boq_progress, name='enter_boq_progress'),

    # View Reports
    path('<int:project_id>/progress/weekly/list/', list_weekly_reports, name='list_weekly_reports'),
    path('progress/weekly/<int:report_id>/', view_weekly_report, name='view_weekly_report'),

    # OM/EG - Review & Approve
    path('progress/weekly/review/', review_weekly_reports, name='review_weekly_reports'),
    path('progress/weekly/<int:report_id>/approve/', approve_weekly_report, name='approve_weekly_report'),
    path('progress/weekly/<int:report_id>/reject/', reject_weekly_report, name='reject_weekly_report'),

    # Export Options (Excel, PDF, Print)
    path('progress/weekly/<int:report_id>/export/', export_report_excel, name='export_report_excel'),
    path('<int:project_id>/progress/weekly/export-all/', export_project_reports_excel, name='export_project_reports_excel'),
    path('<int:project_id>/progress/weekly/export-pdf/', export_project_reports_pdf, name='export_project_reports_pdf'),
    path('<int:project_id>/progress/weekly/print/', print_project_reports, name='print_project_reports'),

    # Excel Template Download & Upload
    path('<int:project_id>/progress/weekly/download-template/', download_progress_template, name='download_progress_template'),
    path('<int:project_id>/progress/weekly/upload-excel/', upload_progress_excel, name='upload_progress_excel'),
]
