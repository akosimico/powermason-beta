# Token System Enhancement

## Overview

The codebase has been enhanced to provide seamless access to all features even when users come from URLs without tokens. The system now supports both token-based and session-based authentication.

## Key Changes

### 1. Automatic Token Generation Middleware

- **File**: `authentication/middleware.py`
- **Class**: `TokenGenerationMiddleware`
- **Purpose**: Automatically generates dashboard tokens for authenticated users who don't have them in their session
- **Behavior**: Runs on every request for authenticated users and ensures they always have a valid token

### 2. Enhanced Token Verification

- **File**: `authentication/utils/tokens.py`
- **Function**: `verify_user_token()`
- **Enhancements**:
  - Automatically generates tokens if none exist in session
  - Handles expired tokens by generating new ones
  - Graceful fallback for missing tokens

### 3. Session-Based URL Support

All major views now support both token-based and session-based access:

#### Authentication URLs
- `dashboard/` - Session-based dashboard
- `dashboard/<token>/<role>/` - Token-based dashboard (legacy)
- `manage-user-profiles/` - Session-based user management
- `manage-user-profiles/<token>/` - Token-based user management (legacy)

#### Project Profiling URLs
- `projects/list/` - Session-based project list
- `projects/<token>/list/<role>/` - Token-based project list (legacy)
- `projects/create/<project_type>/<client_id>/` - Session-based project creation
- `projects/<token>/create/<role>/<project_type>/<client_id>/` - Token-based project creation (legacy)

#### Scheduling URLs
- `scheduling/<project_id>/tasks/` - Session-based task management
- `scheduling/<project_id>/<token>/<role>/tasks/` - Token-based task management (legacy)
- `scheduling/<project_id>/gantt/` - Session-based Gantt view
- `scheduling/<token>/<role>/<project_id>/gantt/` - Token-based Gantt view (legacy)

### 4. URL Helper Utilities

- **File**: `authentication/utils/url_helpers.py`
- **Purpose**: Provides utility functions to generate appropriate URLs based on available tokens
- **Key Functions**:
  - `get_user_token(request)` - Gets or generates user token
  - `get_user_role(request)` - Gets user role
  - `reverse_with_token(request, url_name, ...)` - Generates appropriate URL
  - `get_dashboard_url(request)` - Gets dashboard URL

### 5. Template Tags

- **File**: `authentication/templatetags/url_helpers.py`
- **Purpose**: Template tags for easy URL generation in templates
- **Available Tags**:
  - `{% smart_reverse 'url_name' %}` - Smart URL generation
  - `{% dashboard_url %}` - Dashboard URL
  - `{% project_list_url %}` - Project list URL
  - `{% user_token %}` - Current user token
  - `{% user_role %}` - Current user role

## Usage Examples

### In Views

```python
from authentication.utils.url_helpers import get_dashboard_url, reverse_with_token

def my_view(request):
    # Get dashboard URL (works with or without tokens)
    dashboard_url = get_dashboard_url(request)
    
    # Get project list URL (works with or without tokens)
    project_list_url = reverse_with_token(request, 'project_list')
    
    return render(request, 'template.html', {
        'dashboard_url': dashboard_url,
        'project_list_url': project_list_url,
    })
```

### In Templates

```html
{% load url_helpers %}

<!-- Smart URL generation -->
<a href="{% smart_reverse 'project_list' %}">Projects</a>
<a href="{% dashboard_url %}">Dashboard</a>
<a href="{% project_view_url 'general' project.id %}">View Project</a>

<!-- Get user info -->
<p>Token: {% user_token %}</p>
<p>Role: {% user_role %}</p>
```

## Benefits

1. **Seamless Access**: Users can access all features regardless of how they arrived at the application
2. **Backward Compatibility**: Existing token-based URLs continue to work
3. **Automatic Token Management**: Tokens are generated automatically when needed
4. **Graceful Degradation**: System falls back to session-based access when tokens are unavailable
5. **Easy Migration**: New URLs use session-based access by default

## Migration Guide

### For Developers

1. **Use URL Helpers**: Replace direct `reverse()` calls with `reverse_with_token()` or template tags
2. **Update Templates**: Use the new template tags for URL generation
3. **Test Both Paths**: Ensure your views work with both token-based and session-based URLs

### For Users

- **No Action Required**: The system automatically handles token generation and URL routing
- **Existing Links**: All existing token-based links continue to work
- **New Links**: New links will use session-based access for better user experience

## Configuration

The middleware is automatically enabled in `settings.py`:

```python
MIDDLEWARE = [
    # ... other middleware ...
    "authentication.middleware.TokenGenerationMiddleware",
    "authentication.middleware.LimitMessagesMiddleware",
]
```

## Testing

To test the implementation:

1. **Login without tokens**: Access the application directly without token-based URLs
2. **Verify token generation**: Check that tokens are automatically created in the session
3. **Test URL generation**: Ensure all URLs work with both token and session-based access
4. **Check backward compatibility**: Verify existing token-based URLs still work

## Troubleshooting

### Common Issues

1. **Token not generated**: Check that the user is authenticated and has a UserProfile
2. **URL not found**: Ensure both token-based and session-based URL patterns exist
3. **Permission denied**: Verify the user has the correct role for the requested resource
4. **NoReverseMatch errors**: Use `{% smart_reverse %}` template tag instead of `{% url %}` for URLs that require tokens

### Fixed Issues

#### NoReverseMatch Error for project_costing_dashboard
**Error**: `NoReverseMatch at /dashboard/<token>/<role>/ Reverse for 'project_costing_dashboard' with no arguments not found`

**Solution**: 
1. Updated `authentication/utils/url_helpers.py` to automatically detect and handle URLs that require token and role parameters
2. Updated `templates/partials/_sidebar.html` to use `{% smart_reverse 'project_costing_dashboard' %}` instead of `{% url 'project_costing_dashboard' %}`
3. Added session-based URL patterns for all token-required views

**Files Modified**:
- `authentication/utils/url_helpers.py` - Enhanced `reverse_with_token()` function
- `templates/partials/_sidebar.html` - Updated URL generation
- `progress_monitoring/urls.py` - Added session-based URL pattern

#### UnboundLocalError for UserProfile
**Error**: `UnboundLocalError: cannot access local variable 'UserProfile' where it is not associated with a value`

**Solution**:
1. Moved `UserProfile` import to the top of `authentication/utils/url_helpers.py`
2. Removed local imports inside functions to prevent `UnboundLocalError`
3. Updated exception handling to use generic `Exception` instead of specific model exceptions

**Files Modified**:
- `authentication/utils/url_helpers.py` - Fixed import structure and exception handling

#### ModuleNotFoundError for authentication.utils.models
**Error**: `ModuleNotFoundError: No module named 'authentication.utils.models'`

**Solution**:
1. Fixed the import path in `authentication/utils/url_helpers.py`
2. Changed `from .models import UserProfile` to `from ..models import UserProfile`
3. The correct path is `authentication.models`, not `authentication.utils.models`

**Files Modified**:
- `authentication/utils/url_helpers.py` - Fixed import path for UserProfile model

#### NoReverseMatch Error for mobilization_costs
**Error**: `NoReverseMatch at /dashboard/<token>/<role>/ Reverse for 'mobilization_costs' with no arguments not found`

**Solution**:
1. Added session-based URL pattern for `mobilization_costs`
2. Updated sidebar template to use `{% smart_reverse 'mobilization_costs' %}` instead of `{% url 'mobilization_costs' %}`
3. Fixed all instances of token-required URLs in the sidebar template

**Files Modified**:
- `project_profiling/urls.py` - Added session-based URL pattern for mobilization_costs
- `templates/partials/_sidebar.html` - Updated all token-required URLs to use smart_reverse
- `project_profiling/urls.py` - Added session-based URL pattern for review_pending_project

#### Comprehensive URL Fixes
**Preventive Measures**:
1. Updated all token-required URLs in sidebar template to use `{% smart_reverse %}` tag
2. Added session-based URL patterns for all major token-required views
3. Ensured backward compatibility with existing token-based URLs

**URLs Fixed**:
- `project_costing_dashboard` - Now uses smart_reverse in all instances
- `mobilization_costs` - Added session-based version and updated template
- `progress_monitoring` - Added session-based version
- `review_pending_project` - Added session-based version

#### Sidebar Template Issues Fixed
**Issues**:
1. **Duplicate Cost Tracking sections** - Two identical "Cost Tracking" sections in sidebar
2. **Missing Materials & Equipment submenu** - Button referenced non-existent submenu
3. **Incorrect URL names** - Materials and Equipment links used wrong URL names

**Solutions**:
1. Removed duplicate Cost Tracking section
2. Added complete Materials & Equipment submenu with proper links
3. Fixed URL names to use correct namespaced URLs (`materials_equipment:material_list`, `materials_equipment:equipment_list`)

**Files Modified**:
- `templates/partials/_sidebar.html` - Fixed duplicate sections and added missing submenu

#### Manage Users Authorization Issue Fixed
**Problem**: Manage Users page was throwing "unauthorized" error even for users with correct roles (EG, OM).

**Root Cause**: The user management views had **redundant authorization checks**:
1. `@role_required('EG', 'OM')` decorator (working correctly)
2. `verify_user_token(request, token)` call (failing for session-based access)

**Solution**: Modified all user management views to handle session-based access properly:
- For session-based access (`token=None`): Use user's profile directly since `@role_required` already verified the role
- For token-based access (`token` provided): Use `verify_user_token` as before

**Views Fixed**:
- `manage_user_profiles` - Main user management page
- `add_user` - Add new users
- `edit_user` - Edit existing users  
- `archive_user` - Archive users (EG only)
- `unarchive_user` - Unarchive users (EG only)

**Files Modified**:
- `authentication/views.py` - Fixed authorization logic in all user management views

#### Template URL Issues Fixed
**Problem**: Templates were using token-based URLs even for session-based access, causing URLs like `/add-users/None/` which resulted in unauthorized errors.

**Root Cause**: Templates were using `{% url 'add_user' token=token %}` where `token` was `None` for session-based access, creating invalid URLs.

**Solution**: Updated templates to conditionally use session-based URLs when `token` is `None`:
- `{% if token %}{% url 'add_user' token=token %}{% else %}{% url 'add_user_session' %}{% endif %}`

**Templates Fixed**:
- `templates/users/manage_user_profiles.html` - All user management links
- `templates/users/add_user.html` - Back to manage users links
- `templates/users/edit_user.html` - Back to manage users links

**URLs Fixed in Templates**:
- `manage_user_profiles` → `manage_user_profiles_session`
- `add_user` → `add_user_session`
- `edit_user` → `edit_user_session`
- `archive_user` → `archive_user_session`
- `unarchive_user` → `unarchive_user_session`

### Debug Information

- Check `request.session.get('dashboard_token')` for token presence
- Use `{% user_token %}` template tag to display current token
- Check Django logs for middleware errors
- Use `{% smart_reverse %}` template tag for automatic URL generation
