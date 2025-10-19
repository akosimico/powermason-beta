# Example: How to use the centralized toast system in any app

# ==============================================
# EXAMPLE 1: In any view (e.g., scheduling/views.py)
# ==============================================

from authentication.utils.toast_helpers import set_toast_message

def create_task_view(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save()
            # ✅ Success toast - will show green toast
            set_toast_message(request, f"Task '{task.title}' created successfully!", "success")
            return redirect('task_list')
        else:
            # ❌ Error toast - will show red toast
            set_toast_message(request, "Please fix the errors in the form.", "error")
    
    return render(request, 'task_form.html', {'form': form})

# ==============================================
# EXAMPLE 2: In authentication/views.py
# ==============================================

def update_user_profile(request):
    if request.method == 'POST':
        try:
            # Update logic here
            user_profile = request.user.userprofile
            user_profile.full_name = request.POST.get('full_name')
            user_profile.save()
            
            # ✅ Success toast
            set_toast_message(request, "Profile updated successfully!", "success")
            return redirect('profile')
            
        except Exception as e:
            # ❌ Error toast
            set_toast_message(request, f"Failed to update profile: {str(e)}", "error")
            return redirect('profile')
    
    return render(request, 'profile.html')

# ==============================================
# EXAMPLE 3: In materials_equipment/views.py
# ==============================================

def add_equipment(request):
    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            equipment = form.save()
            # ✅ Success toast
            set_toast_message(request, f"Equipment '{equipment.name}' added to inventory!", "success")
            return redirect('equipment_list')
        else:
            # ⚠️ Warning toast
            set_toast_message(request, "Please check the equipment details and try again.", "warning")
    
    return render(request, 'equipment_form.html', {'form': form})

# ==============================================
# EXAMPLE 4: Using with Django messages
# ==============================================

from django.contrib import messages
from authentication.utils.toast_helpers import set_toast_from_messages

def bulk_operation(request):
    if request.method == 'POST':
        items = request.POST.getlist('items')
        
        success_count = 0
        for item_id in items:
            try:
                # Process each item
                process_item(item_id)
                success_count += 1
            except Exception as e:
                messages.error(request, f"Failed to process item {item_id}: {str(e)}")
        
        if success_count > 0:
            messages.success(request, f"Successfully processed {success_count} items!")
        
        # Convert Django messages to toast
        set_toast_from_messages(request)
        return redirect('results_page')
    
    return render(request, 'bulk_operation.html')

# ==============================================
# EXAMPLE 5: Different toast types
# ==============================================

def example_different_toasts(request):
    # Success (green with checkmark)
    set_toast_message(request, "Operation completed successfully!", "success")
    
    # Error (red with X)
    set_toast_message(request, "Something went wrong!", "error")
    
    # Warning (yellow with warning icon)
    set_toast_message(request, "Please review your input!", "warning")
    
    # Info (blue with info icon)
    set_toast_message(request, "Here's some helpful information!", "info")
    
    return redirect('some_page')
