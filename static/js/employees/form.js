// static/js/employees/form.js
/**
 * Employee Form JavaScript - Enhanced for Add/Edit modes
 * Handles form interactions, validations, and mode-specific behavior
 */

class EmployeeForm {
    constructor() {
        this.form = document.getElementById('employeeForm');
        this.formMode = this.form?.dataset.mode; // 'add' or 'edit'
        this.employeeId = this.form?.dataset.employeeId;
        
        // Form fields
        this.roleField = document.getElementById('id_role');
        this.statusField = document.getElementById('id_status');
        this.emailField = document.getElementById('id_email');
        this.laborCountField = document.getElementById('labor-count-field');
        this.pmInfo = document.getElementById('pm-info');
        this.emailRequiredIndicator = document.getElementById('email-required-indicator');
        this.hireDateField = document.getElementById('id_hire_date');
        this.contractEndDateField = document.getElementById('id_contract_end_date');
        this.phoneField = document.getElementById('id_phone');
        this.departmentField = document.getElementById('id_department');
        
        // Storage keys based on mode
        this.draftKey = this.formMode === 'edit' 
            ? `employee_form_draft_${this.employeeId}` 
            : 'employee_form_draft_new';
        this.autoSaveKey = this.formMode === 'edit' 
            ? `employee_form_autosave_${this.employeeId}` 
            : 'employee_form_autosave_new';
        
        // State tracking
        this.hasUnsavedChanges = false;
        this.originalFormData = {};
        
        this.init();
    }

    init() {
        if (!this.form) return;
        
        this.bindEvents();
        this.setInitialStates();
        this.setDateConstraints();
        this.setupDepartmentAutocomplete();
        this.setupPhoneFormatting();
        this.addKeyboardShortcuts();
        this.trackChanges();
        
        // Load draft only for add mode
        if (this.formMode === 'add') {
            this.loadDraft();
        }
        
        // Store original form data for change detection
        this.captureOriginalData();
    }

    bindEvents() {
        // Role and status change handlers
        if (this.roleField) {
            this.roleField.addEventListener('change', () => this.handleRoleChange());
            this.roleField.addEventListener('change', () => this.autoSave());
        }

        if (this.statusField) {
            this.statusField.addEventListener('change', () => this.handleStatusChange());
            this.statusField.addEventListener('change', () => this.autoSave());
        }

        // Date validation handlers
        if (this.hireDateField) {
            this.hireDateField.addEventListener('change', () => this.validateHireDate());
        }

        if (this.contractEndDateField) {
            this.contractEndDateField.addEventListener('change', () => this.validateContractDate());
        }

        // Form submission validation
        this.form.addEventListener('submit', (e) => this.handleFormSubmit(e));

        // Real-time email validation for PM role
        if (this.emailField) {
            this.emailField.addEventListener('blur', () => this.validateEmailForPM());
            this.emailField.addEventListener('input', () => this.clearEmailErrors());
        }

        // Add validation and auto-save to all form fields
        const allFields = this.form.querySelectorAll('input, select, textarea');
        allFields.forEach(field => {
            field.addEventListener('blur', () => this.validateField(field));
            field.addEventListener('input', () => {
                this.autoSave();
                this.markAsChanged();
            });
            
            // Enhanced focus states
            field.addEventListener('focus', () => {
                field.parentNode.classList.add('ring-4', 'ring-indigo-500/20');
            });
            
            field.addEventListener('blur', () => {
                field.parentNode.classList.remove('ring-4', 'ring-indigo-500/20');
            });
        });

        // Warn about unsaved changes on page unload
        window.addEventListener('beforeunload', (e) => {
            if (this.hasUnsavedChanges && this.formMode === 'add') {
                e.preventDefault();
                e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
                return e.returnValue;
            }
        });
    }

    setInitialStates() {
        // Set initial state based on current selections
        this.handleRoleChange();
        this.handleStatusChange();
        
        // Set default hire date to today if creating new employee
        if (this.formMode === 'add' && this.hireDateField && !this.hireDateField.value) {
            const today = new Date().toISOString().split('T')[0];
            this.hireDateField.value = today;
        }
    }

    setDateConstraints() {
        // Set hire date max to today
        if (this.hireDateField) {
            const today = new Date().toISOString().split('T')[0];
            this.hireDateField.setAttribute('max', today);
        }

        // Set contract end date min to tomorrow
        if (this.contractEndDateField) {
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            this.contractEndDateField.setAttribute('min', tomorrow.toISOString().split('T')[0]);
        }
    }

    handleRoleChange() {
        if (!this.roleField) return;

        const selectedRole = this.roleField.value;
        
        // Handle Labor role - show/hide labor count field
        if (this.laborCountField) {
            if (selectedRole === 'LB' || selectedRole === 'labor') {
                this.showField(this.laborCountField);
            } else {
                this.hideField(this.laborCountField);
                // Reset labor count to 1 for non-labor roles
                const laborCountInput = this.laborCountField.querySelector('input');
                if (laborCountInput) laborCountInput.value = '1';
            }
        }

        // Handle Project Manager role - show info and make email required
        if (this.pmInfo && this.emailField && this.emailRequiredIndicator) {
            if (selectedRole === 'PM' || selectedRole === 'project_manager') {
                this.showField(this.pmInfo);
                this.emailField.setAttribute('required', 'required');
                this.emailRequiredIndicator.classList.remove('hidden');
            } else {
                this.hideField(this.pmInfo);
                this.emailField.removeAttribute('required');
                this.emailRequiredIndicator.classList.add('hidden');
            }
        }
    }

    handleStatusChange() {
        if (!this.statusField || !this.laborCountField) return;

        const selectedStatus = this.statusField.value;
        
        // Show labor count field for contract/temporary status
        if (selectedStatus === 'contract' || selectedStatus === 'temporary') {
            this.showField(this.laborCountField);
        } else {
            this.hideField(this.laborCountField);
        }
    }

    showField(element) {
        if (!element) return;
        
        element.classList.remove('hidden');
        element.style.opacity = '0';
        element.style.transform = 'translateY(-10px)';
        
        setTimeout(() => {
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
            element.style.transition = 'all 0.3s ease-out';
        }, 10);
    }

    hideField(element) {
        if (!element) return;
        
        element.style.opacity = '0';
        element.style.transform = 'translateY(-10px)';
        
        setTimeout(() => {
            element.classList.add('hidden');
        }, 300);
    }

    validateField(field) {
        const isValid = field.checkValidity() && field.value.trim() !== '';
        
        if (isValid) {
            field.classList.remove('border-red-500', 'ring-red-500/20');
            field.classList.add('border-green-500', 'ring-green-500/20');
        } else {
            field.classList.remove('border-green-500', 'ring-green-500/20');
        }
        
        return isValid;
    }

    validateEmailForPM() {
        if (!this.roleField || !this.emailField) return true;

        const role = this.roleField.value;
        if ((role === 'PM' || role === 'project_manager') && !this.emailField.value.trim()) {
            this.showFieldError(this.emailField, 'Email is required for Project Manager role');
            return false;
        }

        this.clearFieldError(this.emailField);
        return true;
    }

    validateHireDate() {
        if (!this.hireDateField) return true;

        const hireDate = new Date(this.hireDateField.value);
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        if (hireDate > today) {
            this.showFieldError(this.hireDateField, 'Hire date cannot be in the future');
            return false;
        }

        this.clearFieldError(this.hireDateField);
        
        // Update contract end date minimum if hire date is set
        if (this.contractEndDateField && this.hireDateField.value) {
            const minContractDate = new Date(hireDate);
            minContractDate.setDate(minContractDate.getDate() + 1);
            this.contractEndDateField.setAttribute('min', minContractDate.toISOString().split('T')[0]);
        }

        return true;
    }

    validateContractDate() {
        if (!this.contractEndDateField || !this.contractEndDateField.value) {
            this.clearFieldError(this.contractEndDateField);
            return true;
        }

        const contractDate = new Date(this.contractEndDateField.value);
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        // Contract end date should be in the future
        if (contractDate <= today) {
            this.showFieldError(this.contractEndDateField, 'Contract end date must be in the future');
            return false;
        }

        // Contract end date should be after hire date
        if (this.hireDateField && this.hireDateField.value) {
            const hireDate = new Date(this.hireDateField.value);
            if (contractDate <= hireDate) {
                this.showFieldError(this.contractEndDateField, 'Contract end date must be after hire date');
                return false;
            }
        }

        this.clearFieldError(this.contractEndDateField);
        return true;
    }

    showFieldError(field, message) {
        this.clearFieldError(field);
        
        field.classList.add('border-red-500', 'ring-red-500');
        
        const errorDiv = document.createElement('p');
        errorDiv.className = 'mt-1 text-sm text-red-600 field-error';
        errorDiv.textContent = message;
        
        field.parentElement.appendChild(errorDiv);
    }

    clearFieldError(field) {
        field.classList.remove('border-red-500', 'ring-red-500');
        
        const existingError = field.parentElement.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }
    }

    clearEmailErrors() {
        if (this.emailField) {
            this.clearFieldError(this.emailField);
        }
    }

    handleFormSubmit(event) {
        let isValid = true;
        const errors = [];

        // Validate required fields
        const requiredFields = this.form.querySelectorAll('[required]');
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                const label = document.querySelector(`label[for="${field.id}"]`);
                const fieldName = label ? label.textContent.replace('*', '').trim() : field.name;
                errors.push(`${fieldName} is required`);
                this.showFieldError(field, `${fieldName} is required`);
            }
        });

        // Validate email for PM role
        if (!this.validateEmailForPM()) {
            isValid = false;
        }

        // Validate dates
        if (!this.validateHireDate()) {
            isValid = false;
        }

        if (!this.validateContractDate()) {
            isValid = false;
        }

        // Validate email format
        if (this.emailField && this.emailField.value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(this.emailField.value)) {
                isValid = false;
                errors.push('Please enter a valid email address');
                this.showFieldError(this.emailField, 'Please enter a valid email address');
            }
        }

        // Prevent submission if validation fails
        if (!isValid) {
            event.preventDefault();
            
            // Show summary error message
            this.showFormErrors(errors);
            
            // Scroll to first error
            const firstError = this.form.querySelector('.border-red-500');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstError.focus();
            }

            this.showNotification('Please fix the highlighted errors', 'error', 4000);
            return false;
        }

        // Show loading state
        this.showSubmissionState();
        
        // Clear draft on successful submission
        this.clearDraft();
        this.clearAutoSave();
        
        // Mark as saved
        this.hasUnsavedChanges = false;

        return true;
    }

    showSubmissionState() {
        const submitButton = this.form.querySelector('button[type="submit"]');
        if (!submitButton) return;

        const originalText = submitButton.innerHTML;
        submitButton.disabled = true;
        
        const loadingText = this.formMode === 'edit' ? 'Updating...' : 'Creating...';
        submitButton.innerHTML = `
            <svg class="w-4 h-4 mr-1.5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            ${loadingText}
        `;
        
        submitButton.classList.add('animate-pulse');
        
        // Restore button after timeout (fallback)
        setTimeout(() => {
            submitButton.innerHTML = originalText;
            submitButton.disabled = false;
            submitButton.classList.remove('animate-pulse');
        }, 10000);
    }

    showFormErrors(errors) {
        // Remove existing error summary
        const existingSummary = this.form.querySelector('.form-error-summary');
        if (existingSummary) {
            existingSummary.remove();
        }

        if (errors.length === 0) return;

        // Create error summary
        const errorSummary = document.createElement('div');
        errorSummary.className = 'form-error-summary bg-red-50 border border-red-200 rounded-md p-4 mb-6';
        
        const errorTitle = document.createElement('h3');
        errorTitle.className = 'text-sm font-medium text-red-800 flex items-center';
        errorTitle.innerHTML = `
            <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
            </svg>
            Please correct the following errors:
        `;
        
        const errorList = document.createElement('ul');
        errorList.className = 'mt-2 text-sm text-red-700 list-disc list-inside space-y-1';
        
        errors.forEach(error => {
            const listItem = document.createElement('li');
            listItem.textContent = error;
            errorList.appendChild(listItem);
        });

        errorSummary.appendChild(errorTitle);
        errorSummary.appendChild(errorList);

        // Insert at top of form
        this.form.insertBefore(errorSummary, this.form.firstChild);

        // Auto-remove after 8 seconds
        setTimeout(() => {
            if (errorSummary.parentNode) {
                errorSummary.remove();
            }
        }, 8000);
    }

    setupPhoneFormatting() {
        if (!this.phoneField) return;

        this.phoneField.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, ''); // Remove non-digits
            
            if (value.length >= 6) {
                if (value.length <= 10) {
                    value = value.replace(/(\d{3})(\d{3})(\d{1,4})/, '($1) $2-$3');
                } else {
                    value = value.replace(/(\d{3})(\d{3})(\d{4})/, '($1) $2-$3');
                }
            } else if (value.length >= 4) {
                value = value.replace(/(\d{3})(\d{1,3})/, '($1) $2');
            }

            e.target.value = value;
            this.validateField(e.target);
        });
    }

    setupDepartmentAutocomplete() {
        if (!this.departmentField) return;

        // Common construction departments
        const commonDepartments = [
            'Construction',
            'Engineering',
            'Safety',
            'Quality Control',
            'Project Management',
            'Operations',
            'Administration',
            'Maintenance',
            'Procurement',
            'Human Resources',
            'Finance',
            'IT Support',
            'Legal',
            'Marketing'
        ];

        // Create datalist for autocomplete
        const datalist = document.createElement('datalist');
        datalist.id = 'department-suggestions';
        
        commonDepartments.forEach(dept => {
            const option = document.createElement('option');
            option.value = dept;
            datalist.appendChild(option);
        });

        this.departmentField.setAttribute('list', 'department-suggestions');
        this.departmentField.parentNode.appendChild(datalist);
    }

    addKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + S to save (prevent browser save dialog)
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                const submitButton = this.form.querySelector('button[type="submit"]');
                if (submitButton && !submitButton.disabled) {
                    submitButton.click();
                }
            }

            // Ctrl/Cmd + Backspace to cancel
            if ((e.ctrlKey || e.metaKey) && e.key === 'Backspace') {
                e.preventDefault();
                const cancelLink = this.form.querySelector('a[href*="list"]');
                if (cancelLink) {
                    if (this.hasUnsavedChanges) {
                        if (confirm('Are you sure you want to cancel? Any unsaved changes will be lost.')) {
                            window.location.href = cancelLink.href;
                        }
                    } else {
                        window.location.href = cancelLink.href;
                    }
                }
            }

            // ESC to focus on cancel button
            if (e.key === 'Escape') {
                const cancelLink = this.form.querySelector('a[href*="list"]');
                if (cancelLink) {
                    cancelLink.focus();
                }
            }
        });
    }

    trackChanges() {
        // Capture original form state for change detection
        this.captureOriginalData();
        
        const allFields = this.form.querySelectorAll('input, select, textarea');
        allFields.forEach(field => {
            field.addEventListener('input', () => {
                this.markAsChanged();
            });
        });
    }

    captureOriginalData() {
        const formData = new FormData(this.form);
        this.originalFormData = {};
        
        for (let [key, value] of formData.entries()) {
            this.originalFormData[key] = value;
        }
    }

    markAsChanged() {
        if (this.formMode === 'add') {
            this.hasUnsavedChanges = true;
        } else {
            // For edit mode, check if data actually changed
            const currentData = this.getCurrentFormData();
            this.hasUnsavedChanges = this.hasDataChanged(currentData);
        }
    }

    getCurrentFormData() {
        const formData = new FormData(this.form);
        const currentData = {};
        
        for (let [key, value] of formData.entries()) {
            currentData[key] = value;
        }
        
        return currentData;
    }

    hasDataChanged(currentData) {
        return Object.keys(currentData).some(key => {
            return currentData[key] !== this.originalFormData[key];
        });
    }

    // Simple auto-save for recovery only (no draft saving)
    autoSave() {
        // Only track changes, don't save drafts
        this.markAsChanged();
    }

    loadDraft() {
        // Only load recovery data for add mode and only if user explicitly requests it
        if (this.formMode !== 'add') return;
        
        const savedDraft = sessionStorage.getItem(this.draftKey);
        if (!savedDraft) return;

        try {
            const { data, timestamp } = JSON.parse(savedDraft);
            
            // Only offer recovery if saved within last hour
            const saveTime = new Date(timestamp);
            const now = new Date();
            const oneHourAgo = new Date(now.getTime() - (60 * 60 * 1000));
            
            if (saveTime < oneHourAgo) {
                sessionStorage.removeItem(this.draftKey);
                return;
            }

            // Ask user if they want to restore (don't auto-restore)
            const shouldRestore = confirm('Found unsaved form data from earlier. Would you like to restore it?');
            if (!shouldRestore) {
                sessionStorage.removeItem(this.draftKey);
                return;
            }

            let hasRestoredData = false;
            Object.keys(data).forEach(key => {
                const field = this.form.querySelector(`[name="${key}"]`);
                if (field && !field.value && data[key]) {
                    field.value = data[key];
                    hasRestoredData = true;
                }
            });

            if (hasRestoredData) {
                this.showNotification('Data restored from previous session', 'info', 3000);
                // Re-initialize dynamic behaviors after loading
                this.handleRoleChange();
                this.handleStatusChange();
            }
        } catch (e) {
            console.error('Error loading recovery data:', e);
            sessionStorage.removeItem(this.draftKey);
        }
    }

    clearDraft() {
        sessionStorage.removeItem(this.draftKey);
    }

    clearAutoSave() {
        sessionStorage.removeItem(this.autoSaveKey);
        if (this.autoSaveTimeout) {
            clearTimeout(this.autoSaveTimeout);
        }
    }

    showNotification(message, type = 'info', duration = 3000) {
        const colors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-yellow-500',
            info: 'bg-blue-500'
        };

        const icons = {
            success: `<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                      </svg>`,
            error: `<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                     <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                   </svg>`,
            warning: `<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                       <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                     </svg>`,
            info: `<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                  </svg>`
        };
        
        const notification = document.createElement('div');
        notification.className = `fixed bottom-4 right-4 ${colors[type]} text-white px-4 py-3 rounded-lg shadow-lg z-50 transition-all duration-300 transform translate-y-2 opacity-0`;
        notification.innerHTML = `
            <div class="flex items-center space-x-2">
                ${icons[type]}
                <span class="text-sm font-medium">${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-y-2', 'opacity-0');
        }, 10);
        
        // Animate out and remove
        setTimeout(() => {
            notification.classList.add('translate-y-2', 'opacity-0');
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }

    // Method to get form completion percentage
    getFormCompletionPercentage() {
        const requiredFields = this.form.querySelectorAll('[required]');
        const filledFields = Array.from(requiredFields).filter(field => field.value.trim() !== '');
        return Math.round((filledFields.length / requiredFields.length) * 100);
    }

    // Method to add helpful tips
    addFieldTips() {
        const tips = {
            'id_role': 'Select the primary role this employee will perform',
            'id_email': 'Required for Project Managers to create system access',
            'id_hire_date': 'The date this employee started working',
            'id_contract_end_date': 'Leave blank for permanent employees',
            'id_labor_count': 'For labor roles, specify number of workers this record represents',
            'id_phone': 'Phone number will be auto-formatted as you type',
            'id_department': 'Start typing to see suggested departments'
        };

        Object.keys(tips).forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (!field) return;

            // Add tooltip on hover
            field.setAttribute('title', tips[fieldId]);
            
            // Add help icon next to label
            const label = document.querySelector(`label[for="${fieldId}"]`);
            if (label && !label.querySelector('.help-icon')) {
                const helpIcon = document.createElement('span');
                helpIcon.className = 'help-icon cursor-help text-gray-400 ml-1';
                helpIcon.innerHTML = '?';
                helpIcon.setAttribute('title', tips[fieldId]);
                helpIcon.style.fontSize = '12px';
                helpIcon.style.fontWeight = 'bold';
                helpIcon.style.display = 'inline-block';
                helpIcon.style.width = '14px';
                helpIcon.style.height = '14px';
                helpIcon.style.lineHeight = '14px';
                helpIcon.style.textAlign = 'center';
                helpIcon.style.borderRadius = '50%';
                helpIcon.style.border = '1px solid #9CA3AF';
                label.appendChild(helpIcon);
            }
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const employeeForm = new EmployeeForm();
    
    if (employeeForm.form) {
        // Setup additional features
        employeeForm.addFieldTips();
        
        // Only save recovery data on page unload for add mode
        if (employeeForm.formMode === 'add') {
            window.addEventListener('beforeunload', () => {
                const formData = new FormData(employeeForm.form);
                const formDataObj = {};
                
                for (let [key, value] of formData.entries()) {
                    if (value && value.toString().trim() !== '') {
                        formDataObj[key] = value;
                    }
                }
                
                // Only save if there's meaningful data and user has made changes
                if (Object.keys(formDataObj).length > 2 && employeeForm.hasUnsavedChanges) { // More than just csrf token
                    sessionStorage.setItem(employeeForm.draftKey, JSON.stringify({
                        data: formDataObj,
                        timestamp: new Date().toISOString()
                    }));
                }
            });
        }

        // Clear recovery data on successful form submission
        employeeForm.form.addEventListener('submit', (e) => {
            if (e.defaultPrevented) return; // Don't clear if validation failed
            
            setTimeout(() => {
                employeeForm.clearDraft();
            }, 1000);
        });

        // Add helpful keyboard shortcut hints to submit button
        const submitButton = employeeForm.form.querySelector('button[type="submit"]');
        if (submitButton) {
            const actionText = employeeForm.formMode === 'edit' ? 'Update' : 'Create';
            submitButton.setAttribute('title', `Ctrl+S to ${actionText}`);
        }

        // Show form mode indicator in console for debugging
        console.log(`Employee form initialized in ${employeeForm.formMode} mode`);
        if (employeeForm.employeeId) {
            console.log(`Editing employee ID: ${employeeForm.employeeId}`);
        }
    }
});