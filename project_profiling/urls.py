from django.urls import path
from . import views
from . import cost_estimation_views
from . import file_preview_views
from . import quotation_views
from .cost_dashboard_views import (
    project_detail_cost_dashboard,
    api_project_cost_summary,
    api_add_quick_expense
)

urlpatterns = [
    # ==============================================
    # DEFAULT & AUTHENTICATION
    # ==============================================
    path('', views.project_list_default, name='project_list_default'),

    # ==============================================
    # PROJECT MANAGEMENT
    # ==============================================
    # Session-based project list
    path('list/', views.project_list_signed_with_role, name='project_list'),
    
    # General / Direct project lists (session-based)
    path('general/', views.general_projects_list, name='project_list_general_contractor'),
    path('direct/', views.direct_projects_list, name='project_list_direct_client'),

    # Create project - Session-based
    path('create/<str:project_type>/<str:client_id>/', views.project_create, name='project_create'),

    # Edit project - Session-based
    path('edit/<int:pk>/', views.project_edit_signed_with_role, name='project_edit'),
    
    # View project - Session-based
    path('view/<str:project_source>/<int:pk>/', views.project_view, name='project_view'),
    
    # Update project status
    path('projects/<int:project_id>/update-status/', views.update_project_status, name='update_project_status'),

    # Archive/Unarchive project - Session-based
    path('delete/<str:project_type>/<int:pk>/', views.project_archive_signed_with_role, name='project_archive'),
    path('unarchive/<str:project_type>/<int:pk>/', views.project_unarchive_signed_with_role, name='project_unarchive'),
    path('archived/<str:project_type>/', views.archived_projects_list, name='archived_projects_list'),



    # ==============================================
# BUDGET WORKFLOW (Simplified - No Token)
# ==============================================

# Step 1: Budget Approval
path('<int:project_id>/approve-budget/', views.approve_budget, name='approve_budget'),

# Step 2: Budget Planning (define scopes and categories)
path('<int:project_id>/budget-planning/', views.budget_planning, name='budget_planning'),

# Budget management
path('<int:project_id>/budgets/<int:budget_id>/edit-ajax/', views.edit_budget_ajax, name='edit_budget_ajax'),
path('<int:project_id>/budgets/<int:budget_id>/delete/', views.delete_budget, name='delete_budget'),

# ==============================================
# FUND ALLOCATION (Simplified - No Token)
# ==============================================
path('<int:project_id>/scopes/delete/', views.delete_scope, name='delete_scope'),
path('<int:project_id>/scopes/restore/', views.restore_scope, name='restore_scope'),
path('<int:project_id>/scopes/<int:scope_id>/edit/', views.edit_scope, name='edit_scope'),
# Fund Allocation Overview
path('<int:project_id>/allocate/', views.project_allocate_budget, name='project_allocate_budget'),


# Allocate funds to specific category
path('<int:project_id>/budgets/<int:budget_id>/allocate/', views.allocate_fund_to_category, name='allocate_fund_to_category'),

# Delete allocation
path('<int:project_id>/budgets/<int:budget_id>/allocations/<int:allocation_id>/soft-delete/', 
         views.soft_delete_allocation, 
         name='soft_delete_allocation'),
         
    path('<int:project_id>/budgets/<int:budget_id>/allocations/<int:allocation_id>/hard-delete/', 
         views.hard_delete_allocation, 
         name='hard_delete_allocation'),
 path('<int:project_id>/budgets/<int:budget_id>/allocations/<int:allocation_id>/restore/', 
         views.restore_allocation, 
         name='restore_allocation'),
 
 path('<int:project_id>/add-expense/', views.add_expense, name='add_expense'),
path('<int:project_id>/categories/<int:category_id>/allocation/', views.get_category_allocation, name='get_category_allocation'),
    # ==============================================
    # DASHBOARD & REPORTING
    # ==============================================
    # Project costing dashboard (overview - all projects) - Session-based
    path('costing/', views.project_costing_dashboard, name='project_costing_dashboard'),

    # Detailed cost dashboard for specific project - Session-based
    path('costing/<int:project_id>/', project_detail_cost_dashboard, name='project_detail_cost_dashboard'),

    # Cost tracking API endpoints
    path('api/projects/<int:project_id>/cost-summary/', api_project_cost_summary, name='api_project_cost_summary'),
    path('api/projects/<int:project_id>/add-expense/', api_add_quick_expense, name='api_add_quick_expense'),

    # ==============================================
    # DRAFT PROJECTS
    # ==============================================
    # Draft projects list
    path('drafts/', views.draft_projects_list, name='draft_projects_list'),

    # Edit draft project
    path('drafts/<int:draft_id>/edit/', views.edit_draft_project, name='edit_draft_project'),

    # Delete draft project
    path('drafts/<int:draft_id>/delete/', views.delete_draft_project, name='delete_draft_project'),


    # ==============================================
    # STAGING & REVIEW
    # ==============================================
    # Review a single pending project (renamed from staging) - Session-based
    path('pending/<int:project_id>/review/', views.review_pending_project, name='review_pending_project'),

    # ==============================================
    # UTILITIES
    # ==============================================
    # Search project managers
    path('search/project-managers/', views.search_project_managers, name='search_project_managers'),

    # ==============================================
    # DOCUMENT LIBRARY
    # ==============================================
    path('documents/', views.document_library, name='document_library'),
    path('api/document-stats/', views.api_document_stats, name='api_document_stats'),
    path('api/documents/', views.api_documents_list, name='api_documents_list'),
    path('api/documents/<int:doc_id>/', views.api_document_detail, name='api_document_detail'),
    path('api/document-upload/', views.api_document_upload, name='api_document_upload'),
    path('api/documents/<int:doc_id>/download/', views.api_document_download, name='api_document_download'),
    path('api/documents/<int:doc_id>/versions/', views.api_document_versions, name='api_document_versions'),
    path('api/documents/<int:doc_id>/archive/', views.api_document_archive, name='api_document_archive'),
    path('api/documents/<int:doc_id>/restore/', views.api_document_restore, name='api_document_restore'),
    path('api/projects-list/', views.api_projects_list, name='api_projects_list'),
    path('api/project-list/', views.api_projects_list, name='api_project_list'),  # Alias for compatibility

    # ==============================================
    # COST TRACKING (Week 3)
    # ==============================================
    # Subcontractor Management
    path('subcontractors/', views.subcontractor_list, name='subcontractor_list'),
    path('api/subcontractors/', views.api_subcontractor_list, name='api_subcontractor_list'),
    path('api/subcontractors/<int:subcon_id>/', views.api_subcontractor_detail, name='api_subcontractor_detail'),
    path('api/subcontractors/<int:subcon_id>/payments/', views.api_subcontractor_payments, name='api_subcontractor_payments'),
    path('api/subcontractors/<int:subcon_id>/payments/create/', views.api_create_payment, name='api_create_payment'),

    
    # Cost Estimation API
    path('api/cost-estimation/', cost_estimation_views.CostEstimationAPIView.as_view(), name='api_cost_estimation'),
    path('api/cost-estimation/options/', cost_estimation_views.get_estimation_options_api, name='api_estimation_options'),
    
    # File Preview and Data Extraction API
    path('api/file-preview/', file_preview_views.FilePreviewAPIView.as_view(), name='api_file_preview'),
    path('api/file-preview/legacy/', file_preview_views.file_preview_api, name='api_file_preview_legacy'),
    path('api/save-extracted-data/', file_preview_views.save_extracted_data_api, name='api_save_extracted_data'),
    
    # BOQ Upload API
    path('api/boq-upload/', file_preview_views.BOQUploadAPIView.as_view(), name='api_boq_upload'),
    path('boq/template/', file_preview_views.download_boq_template, name='download_boq_template'),
    path('boq/template/blank/', file_preview_views.download_blank_boq_template, name='download_blank_boq_template'),
    path('boq/template/electrical/', file_preview_views.download_electrical_boq_template, name='download_electrical_boq_template'),
    path('boq/template/mechanical/', file_preview_views.download_mechanical_boq_template, name='download_mechanical_boq_template'),
    path('boq/template/civil/', file_preview_views.download_civil_boq_template, name='download_civil_boq_template'),
    path('boq/template/architectural/', file_preview_views.download_architectural_boq_template, name='download_architectural_boq_template'),
    path('boq/preview/', file_preview_views.boq_preview_test, name='boq_preview_test'),
        path('api/project-type-cost-data/<int:project_type_id>/', file_preview_views.check_project_type_cost_data, name='check_project_type_cost_data'),
        path('api/project-type-boq-breakdown/<int:project_type_id>/', file_preview_views.get_project_type_boq_breakdown, name='get_project_type_boq_breakdown'),
        path('api/project-type-auto-configure/<int:project_type_id>/', file_preview_views.auto_configure_project_type_costs, name='auto_configure_project_type_costs'),
        path('api/boq-export/<int:project_id>/', file_preview_views.export_boq_to_excel, name='export_boq_to_excel'),
        
    # ==============================================
    # TOAST NOTIFICATIONS
    # ==============================================
    path('clear-toast-session/', views.clear_toast_session, name='clear_toast_session'),
    
    # ==============================================
    # GEOCODING API (CORS Proxy)
    # ==============================================
    path('api/geocoding/reverse/', views.reverse_geocode, name='reverse_geocode'),
    path('api/geocoding/search/', views.forward_geocode, name='forward_geocode'),
    
    # ==============================================
    # QUOTATION MANAGEMENT
    # ==============================================
    path('<int:project_id>/quotations/upload/', quotation_views.upload_quotation, name='upload_quotation'),
    path('<int:project_id>/quotations/list/', quotation_views.list_quotations, name='list_quotations'),
    path('<int:project_id>/quotations/<int:quotation_id>/approve/', quotation_views.approve_quotation, name='approve_quotation'),
    path('<int:project_id>/quotations/<int:quotation_id>/delete/', quotation_views.delete_quotation, name='delete_quotation'),
    path('<int:project_id>/rfs/download/', quotation_views.download_rfs, name='download_rfs'),
    
    # ==============================================
    # RFS DOWNLOAD (moved to quotation_views)
    # ==============================================
    # path('rfs/download/<path:file_path>/', views.download_rfs_file, name='download_rfs_file'),
]