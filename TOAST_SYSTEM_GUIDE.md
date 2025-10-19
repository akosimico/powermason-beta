# Toast Notification System Guide

## Overview

The toast notification system is now centralized and can be used across all apps in the project. It provides a consistent way to show success, error, warning, and info messages to users.

## 🚀 Quick Start

### 1. Basic Usage in Any View

```python
from authentication.utils.toast_helpers import set_toast_message

def my_view(request):
    # Do some operation
    try:
        # Your business logic here
        result = perform_operation()
        
        # Set success toast
        set_toast_message(request, "Operation completed successfully!", "success")
        return redirect('success_page')
        
    except Exception as e:
        # Set error toast
        set_toast_message(request, f"Error: {str(e)}", "error")
        return redirect('error_page')
```

### 2. Using with Django Messages

```python
from django.contrib import messages
from authentication.utils.toast_helpers import set_toast_from_messages

def my_view(request):
    # Add Django message
    messages.success(request, "Data saved successfully!")
    
    # Convert to toast
    set_toast_from_messages(request)
    return redirect('next_page')
```

## 📱 Available Toast Types

- `success` - Green toast with checkmark icon
- `error` - Red toast with X icon  
- `warning` - Yellow toast with warning icon
- `info` - Blue toast with info icon

## 🔧 Implementation Examples

### In Project Profiling App

```python
# project_profiling/views.py
from authentication.utils.toast_helpers import set_toast_message

def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            set_toast_message(request, f"Project '{project.name}' created successfully!", "success")
            return redirect('project_list')
        else:
            set_toast_message(request, "Please fix the errors below.", "error")
    
    return render(request, 'project_form.html', {'form': form})
```

### In Authentication App

```python
# authentication/views.py
from authentication.utils.toast_helpers import set_toast_message

def update_profile(request):
    if request.method == 'POST':
        # Update profile logic
        set_toast_message(request, "Profile updated successfully!", "success")
        return redirect('profile')
    
    return render(request, 'profile.html')
```

### In Scheduling App

```python
# scheduling/views.py
from authentication.utils.toast_helpers import set_toast_message

def create_task(request):
    if request.method == 'POST':
        # Create task logic
        set_toast_message(request, "Task created and assigned!", "success")
        return redirect('task_list')
    
    return render(request, 'task_form.html')
```

## 🎨 Frontend Integration

The toast system automatically works with the existing `base.html` template. The JavaScript will:

1. Check for `request.session.show_toast` on page load
2. Display the toast using `showProjectToast()`
3. Automatically clear the session data via `/clear-toast-session/`

### Custom Toast Display

If you need custom toast display, you can use the existing JavaScript functions:

```javascript
// In your template
showProjectToast("Custom message", "success");
showProjectToast("Error occurred", "error");
showProjectToast("Warning message", "warning");
showProjectToast("Info message", "info");
```

## 🔄 Migration from Old System

### Before (App-specific)
```python
# Old way - tied to projects app
request.session['show_toast'] = {'message': 'Success!', 'type': 'success'}
```

### After (Centralized)
```python
# New way - works everywhere
from authentication.utils.toast_helpers import set_toast_message
set_toast_message(request, "Success!", "success")
```

## 🛠️ Advanced Usage

### Batch Operations with Multiple Toasts

```python
def batch_operation(request):
    results = []
    for item in items:
        try:
            process_item(item)
            results.append(f"✓ {item.name}")
        except Exception as e:
            results.append(f"✗ {item.name}: {str(e)}")
    
    # Show summary
    success_count = len([r for r in results if r.startswith('✓')])
    error_count = len([r for r in results if r.startswith('✗')])
    
    if error_count == 0:
        set_toast_message(request, f"All {success_count} items processed successfully!", "success")
    else:
        set_toast_message(request, f"Processed {success_count} items, {error_count} errors occurred.", "warning")
    
    return redirect('results_page')
```

### Conditional Toasts

```python
def conditional_view(request):
    if some_condition:
        set_toast_message(request, "Special condition met!", "info")
    else:
        set_toast_message(request, "Normal operation completed.", "success")
    
    return redirect('next_page')
```

## 🎯 Best Practices

1. **Use appropriate message types**: success for positive actions, error for failures, warning for caution, info for general information
2. **Keep messages concise**: Users should quickly understand what happened
3. **Be specific**: "User John Doe created successfully" vs "User created"
4. **Use consistent language**: Follow the same tone across your app
5. **Test thoroughly**: Ensure toasts work across different browsers and devices

## 🔍 Troubleshooting

### Toast not showing?
- Check that `base.html` is being extended
- Verify the session data is set correctly
- Check browser console for JavaScript errors

### Toast showing multiple times?
- Ensure you're not setting the session multiple times
- Check that the clear session endpoint is working

### Custom styling needed?
- Modify the `showProjectToast()` function in `base.html`
- Or create your own toast display function
