// project_form_enhanced.js
// Enhanced JavaScript for production-ready project form

document.addEventListener('DOMContentLoaded', function() {
    // Initialize form functionality
    initTabNavigation();
    initFormValidation();
    initAutoComplete();
    initProgressTracking();
    initDraftSave();
    initFileUploads();
    
    // Tab navigation system
    function initTabNavigation() {
        const tabs = document.querySelectorAll('.tab-button');
        const tabContents = document.querySelectorAll('.tab-content');
        const prevButton = document.getElementById('prev-tab');
        const nextButton = document.getElementById('next-tab');
        let currentTab = 0;
        
        tabs.forEach((tab, index) => {
            tab.addEventListener('click', () => switchToTab(index));
        });
        
        prevButton.addEventListener('click', () => {
            if (currentTab > 0) switchToTab(currentTab - 1);
        });
        
        nextButton.addEventListener('click', () => {
    if (validateCurrentTab() && currentTab < tabs.length - 1) {
        switchToTab(currentTab + 1);
    } else if (currentTab === tabs.length - 1) {
        // Last tab - submit the form naturally
        const form = document.querySelector('form');
        if (form) {
            form.submit();
        }
    }
});
        
        function switchToTab(index) {
            // Update tab buttons
            tabs.forEach((tab, i) => {
                tab.classList.toggle('active', i === index);
                tab.classList.toggle('border-blue-500', i === index);
                tab.classList.toggle('text-blue-600', i === index);
                tab.classList.toggle('border-transparent', i !== index);
                tab.classList.toggle('text-gray-500', i !== index);
            });
            
            // Update tab content
            tabContents.forEach((content, i) => {
                content.classList.toggle('hidden', i !== index);
            });
            
            // Update navigation buttons
            prevButton.disabled = index === 0;
            nextButton.textContent = index === tabs.length - 1 ? 'Create Project' : 'Next';
            
            // Update progress bar
            updateProgressBar(index);
            
            currentTab = index;
            
            // Scroll to top of form
            document.querySelector('.max-w-6xl').scrollIntoView({ behavior: 'smooth' });
        }
        
        function validateCurrentTab() {
            const currentTabContent = tabContents[currentTab];
            const requiredFields = currentTabContent.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    showFieldError(field, 'This field is required');
                    isValid = false;
                } else {
                    clearFieldError(field);
                }
            });
            
            return isValid;
        }
    }
    
    // Form validation system
function initFormValidation() {
    const form = document.querySelector('form');
    const inputs = form.querySelectorAll('input, select, textarea');
    let isSubmitting = false; // Add submission flag
    
    inputs.forEach(input => {
        input.addEventListener('blur', () => validateField(input));
        input.addEventListener('input', () => clearFieldError(input));
    });
    
    // Form submission is now handled naturally by the browser
    
    // Remove form submit event listener - let the form submit naturally
    // The draft save is handled by the draft button click event
    
    // Form submission is handled naturally by the browser
}
    
    function validateField(field) {
        const value = field.value.trim();
        const fieldType = field.type;
        const fieldName = field.name;
        
        // Required field validation
        if (field.hasAttribute('required') && !value) {
            showFieldError(field, 'This field is required');
            return false;
        }
        
        // Email validation
        if (fieldType === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                showFieldError(field, 'Please enter a valid email address');
                return false;
            }
        }
        
        // Date validation
        if (fieldType === 'date' && value) {
            const date = new Date(value);
            const today = new Date();
            
            if (fieldName === 'start_date' && date < today.setHours(0,0,0,0)) {
                showFieldError(field, 'Start date cannot be in the past');
                return false;
            }
            
            if (fieldName === 'target_completion_date') {
                const startDate = document.querySelector('[name="start_date"]').value;
                if (startDate && date <= new Date(startDate)) {
                    showFieldError(field, 'Completion date must be after start date');
                    return false;
                }
            }
        }
        
        // GPS coordinates validation
        if (fieldName === 'gps_coordinates' && value) {
            const coordRegex = /^-?([1-8]?[1-9]|[1-9]0)\.{1}\d{1,6},-?([1]?[1-7][1-9]|[1]?[1-8][0]|[1-9]?[0-9])\.{1}\d{1,6}$/;
            if (!coordRegex.test(value)) {
                showFieldError(field, 'Please enter valid coordinates (latitude, longitude)');
                return false;
            }
        }
        
        clearFieldError(field);
        showFieldSuccess(field);
        return true;
    }
    
    function validateForm() {
        const inputs = document.querySelectorAll('input[required], select[required], textarea[required]');
        let isValid = true;
        
        inputs.forEach(input => {
            if (!validateField(input)) {
                isValid = false;
            }
        });
        
        if (!isValid) {
            showProjectToast('Please correct the errors before submitting', 'error');
        }
        
        return isValid;
    }
    
    function showFieldError(field, message) {
        clearFieldError(field);
        field.classList.add('field-error');
        
        const errorElement = document.createElement('p');
        errorElement.className = 'mt-1 text-sm text-red-600 flex items-center field-error-message';
        errorElement.innerHTML = `
            <svg class="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
            </svg>
            ${message}
        `;
        
        field.parentNode.appendChild(errorElement);
    }
    
    function clearFieldError(field) {
        field.classList.remove('field-error');
        const errorMessage = field.parentNode.querySelector('.field-error-message');
        if (errorMessage) {
            errorMessage.remove();
        }
    }
    
    function showFieldSuccess(field) {
        if (field.value.trim()) {
            field.classList.add('field-success');
            setTimeout(() => field.classList.remove('field-success'), 2000);
        }
    }
    
    // Simplified autocomplete functionality
    function initAutoComplete() {
        const pmInput = document.getElementById('project_manager_input');
        const pmIdInput = document.getElementById('project_manager_id');
        const suggestions = document.getElementById('pm_suggestions');
        const pmDisplay = document.getElementById('assigned_pm_display');
        
        if (!pmInput || !pmIdInput || !suggestions || !pmDisplay) return;
        
        let debounceTimer;
        
        pmInput.addEventListener('input', function() {
            const query = this.value.trim();
            
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                if (query.length >= 2) {
                    searchProjectManagers(query);
                } else {
                    hideSuggestions();
                }
            }, 300);
        });
        
        pmInput.addEventListener('focus', function() {
            if (this.value.length >= 2) {
                showSuggestions();
            }
        });
        
        document.addEventListener('click', function(e) {
            if (!pmInput.contains(e.target) && !suggestions.contains(e.target)) {
                hideSuggestions();
            }
        });
        
        function searchProjectManagers(query) {
            // You can replace this with actual API call to your Django backend
            // Example: fetch('/api/search-project-managers/?q=' + encodeURIComponent(query))
            
            // Mock data for demonstration
            const mockResults = [
                { id: 1, full_name: 'John Doe', email: 'john@example.com', department: 'Engineering' },
                { id: 2, full_name: 'Jane Smith', email: 'jane@example.com', department: 'Construction' },
                { id: 3, full_name: 'Mike Johnson', email: 'mike@example.com', department: 'Project Management' },
                { id: 4, full_name: 'Sarah Wilson', email: 'sarah@example.com', department: 'Architecture' }
            ].filter(pm => pm.full_name.toLowerCase().includes(query.toLowerCase()));
            
            displaySuggestions(mockResults);
        }
        
        function displaySuggestions(results) {
            suggestions.innerHTML = '';
            
            if (results.length === 0) {
                suggestions.innerHTML = '<li class="px-4 py-3 text-gray-500 text-sm">No project managers found</li>';
            } else {
                results.forEach(pm => {
                    const li = document.createElement('li');
                    li.className = 'px-4 py-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-b-0';
                    li.innerHTML = `
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="font-medium text-gray-900">${pm.full_name}</div>
                                <div class="text-sm text-gray-500">${pm.email}</div>
                            </div>
                            <div class="text-xs text-gray-400">${pm.department}</div>
                        </div>
                    `;
                    
                    li.addEventListener('click', () => selectProjectManager(pm));
                    suggestions.appendChild(li);
                });
            }
            
            showSuggestions();
        }
        
        function selectProjectManager(pm) {
            pmInput.value = pm.full_name;
            pmIdInput.value = pm.id;
            
            pmDisplay.innerHTML = `
                <div class="flex items-center p-3 bg-green-50 border border-green-200 rounded-lg">
                    <div class="flex-shrink-0">
                        <svg class="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                        </svg>
                    </div>
                    <div class="ml-3">
                        <p class="text-sm font-medium text-green-800">Assigned to: ${pm.full_name}</p>
                        <p class="text-xs text-green-600">${pm.email} • ${pm.department}</p>
                    </div>
                </div>
            `;
            
            hideSuggestions();
            showToast(`${pm.full_name} assigned as Project Manager`, 'success');
        }
        
        function showSuggestions() {
            suggestions.classList.remove('hidden');
        }
        
        function hideSuggestions() {
            suggestions.classList.add('hidden');
        }
    }
    
    // File upload handling
    function initFileUploads() {
        // Contract Agreement file upload
        const contractButton = document.getElementById('contract-upload-btn');
        const contractInput = document.getElementById('id_contract_agreement');
        const contractDisplay = document.getElementById('contract-file-display');
        
        if (contractButton && contractInput) {
            contractButton.addEventListener('click', function() {
                const input = document.createElement('input');
                input.type = 'file';
                input.accept = '.pdf,.doc,.docx,.txt';
                input.onchange = function(event) {
                    const file = event.target.files[0];
                    if (file) {
                        // Store the file reference
                        contractInput.value = file.name;
                        updateFileDisplay(contractDisplay, file.name, 'contract');
                        showToast(`Contract file "${file.name}" selected`, 'success');
                    }
                };
                input.click();
            });
        }
        
        // Permits & Licenses file upload
        const permitsButton = document.getElementById('permits-upload-btn');
        const permitsInput = document.getElementById('id_permits_licenses');
        const permitsDisplay = document.getElementById('permits-file-display');
        
        if (permitsButton && permitsInput) {
            permitsButton.addEventListener('click', function() {
                const input = document.createElement('input');
                input.type = 'file';
                input.accept = '.pdf,.doc,.docx,.txt';
                input.multiple = true;
                input.onchange = function(event) {
                    const files = Array.from(event.target.files);
                    if (files.length > 0) {
                        const fileNames = files.map(f => f.name).join(', ');
                        permitsInput.value = fileNames;
                        updateFileDisplay(permitsDisplay, fileNames, 'permits');
                        showToast(`${files.length} permit file(s) selected`, 'success');
                    }
                };
                input.click();
            });
        }
    }
    
    function updateFileDisplay(displayElement, fileName, type) {
        if (displayElement) {
            displayElement.innerHTML = `
                <div class="flex items-center p-2 bg-blue-50 border border-blue-200 rounded-lg">
                    <svg class="w-4 h-4 text-blue-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 0v12h8V6.414L12.586 4H6z" clip-rule="evenodd"></path>
                    </svg>
                    <span class="text-sm text-blue-700 font-medium">${fileName}</span>
                    <button type="button" class="ml-auto text-blue-500 hover:text-blue-700" onclick="clearFile('${type}')">
                        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                        </svg>
                    </button>
                </div>
            `;
        }
    }
    
    // Progress tracking
    function initProgressTracking() {
        updateProgressBar(0);
    }
    
    function updateProgressBar(tabIndex) {
        const totalTabs = 4;
        const progress = ((tabIndex + 1) / totalTabs) * 100;
        const progressBar = document.querySelector('.bg-blue-600');
        
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }
    }
    
    // Draft save functionality (manual only)
    function initDraftSave() {
        // Save as draft button functionality
        const draftButton = document.getElementById('save-draft-btn');
        console.log('Draft button found:', draftButton); // Check if button is found

        if (draftButton) {
            draftButton.addEventListener('click', function(e) {
                console.log('Draft button clicked!'); // Check if click is registered
                e.preventDefault();
                saveDraft();
            });
        } else {
            console.log('Draft button not found - check ID'); // Debug message
        }
        
        function saveDraft() {
            const formData = new FormData(document.querySelector('form'));
            saveDraftData(formData, false); // false for manual save
        }
        
function saveDraftData(formData, isAutoSave = false) {
    // Don't auto-save if form is being submitted
    if (window.isSubmitting) return;
    
    console.log('Starting draft save...', isAutoSave ? 'auto' : 'manual');
    
    // Add draft flag to form data
    formData.append('save_as_draft', 'true');
    
    // Get CSRF token properly
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    console.log('CSRF Token found:', !!csrfToken);
    console.log('Request URL:', window.location.href);
    
    // Log some form data entries (not all to avoid spam)
    console.log('save_as_draft:', formData.get('save_as_draft'));
    console.log('project_name:', formData.get('project_name'));
    
    fetch(window.location.href, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken,
            'Accept': 'application/json'
        }
    })
    .then(response => {
        console.log('Response status:', response.status);
        console.log('Response content-type:', response.headers.get('content-type'));
        
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            // Log the actual HTML response to see what's being returned
            return response.text().then(text => {
                console.log('HTML response received (first 500 chars):', text.substring(0, 500));
                throw new Error('Server returned HTML instead of JSON');
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('JSON response received:', data);
        if (data.success && !isAutoSave) {
            showProjectToast('Draft saved successfully', 'success');
            // Redirect to draft projects list after successful save
            setTimeout(() => {
                window.location.href = '/projects/drafts/';
            }, 1500);
        } else if (!data.success) {
            showProjectToast('Draft save failed: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('Draft save error:', error);
        if (!isAutoSave) {
            showProjectToast('Failed to save draft: ' + error.message, 'error');
        }
    });
}}
    
    // Utility functions
    function showToast(message, type = 'info', duration = 5000) {
        const container = document.getElementById('toast-container');
        if (!container) return;
        
        const toast = document.createElement('div');
        
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="flex items-center">
                <div class="flex-shrink-0">
                    ${getToastIcon(type)}
                </div>
                <div class="ml-3">
                    <p class="text-sm font-medium">${message}</p>
                </div>
                <div class="ml-auto pl-3">
                    <button type="button" class="inline-flex text-gray-400 hover:text-gray-600" onclick="this.closest('.toast').remove()">
                        <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                        </svg>
                    </button>
                </div>
            </div>
        `;
        
        container.appendChild(toast);
        
        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Auto remove
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
    
    function getToastIcon(type) {
        const icons = {
            success: '<svg class="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>',
            error: '<svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path></svg>',
            warning: '<svg class="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path></svg>',
            info: '<svg class="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path></svg>'
        };
        return icons[type] || icons.info;
    }
    
    function showLoadingOverlay() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.remove('hidden');
        }
    }
    
    function hideLoadingOverlay() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.add('hidden');
        }
    }
    
    // Global functions for template callbacks
    window.toggleAutoFillDetails = function() {
        showToast('Auto-fill details feature coming soon', 'info');
    };
    
    window.dismissNotification = function(element) {
        element.style.transform = 'translateX(100%)';
        element.style.opacity = '0';
        setTimeout(() => element.remove(), 300);
    };
    
    window.getCurrentLocation = function() {
        if ('geolocation' in navigator) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    const lat = position.coords.latitude.toFixed(6);
                    const lng = position.coords.longitude.toFixed(6);
                    const coordsInput = document.getElementById('id_gps_coordinates');
                    if (coordsInput) {
                        coordsInput.value = `${lat}, ${lng}`;
                        showToast('Location captured successfully', 'success');
                    }
                },
                function(error) {
                    showToast('Unable to get current location', 'error');
                }
            );
        } else {
            showToast('Geolocation is not supported by this browser', 'error');
        }
    };
    
    window.clearFile = function(type) {
        if (type === 'contract') {
            const input = document.getElementById('id_contract_agreement');
            const display = document.getElementById('contract-file-display');
            if (input) input.value = '';
            if (display) display.innerHTML = '';
        } else if (type === 'permits') {
            const input = document.getElementById('id_permits_licenses');
            const display = document.getElementById('permits-file-display');
            if (input) input.value = '';
            if (display) display.innerHTML = '';
        }
        showToast('File removed', 'info');
    };
    
    // Form submission handler
    window.submitForm = function() {
        console.log('submitForm called');
        
        // Show loading state on all create buttons
        const createButtons = document.querySelectorAll('#create-project-btn, #create-project-btn-mobile, #create-project-btn-mobile-top');
        createButtons.forEach(button => {
            if (button) {
                const originalContent = button.innerHTML;
                button.innerHTML = `
                    <svg class="animate-spin w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Creating...
                `;
                button.disabled = true;
                button.classList.add('opacity-50', 'cursor-not-allowed');
                button.dataset.originalContent = originalContent;
            }
        });
        
        // Check client selection if client selection is shown
        const clientSelect = document.getElementById('clientSelect') || document.getElementById('clientSelectMobile');
        if (clientSelect) {
            // Check both the selectedClient variable and the actual select value
            const selectedValue = clientSelect.value;
            const hasSelectedClient = window.selectedClient && window.selectedClient.id;
            const hasSelectedValue = selectedValue && selectedValue !== '';
            
            console.log('Form submission validation:');
            console.log('  clientSelect exists:', !!clientSelect);
            console.log('  selectedValue:', selectedValue);
            console.log('  hasSelectedClient:', hasSelectedClient);
            console.log('  hasSelectedValue:', hasSelectedValue);
            console.log('  selectedClient:', window.selectedClient);
            
            // If we have a selectedClient, that's sufficient (Select2 might not update native select immediately)
            if (!hasSelectedClient && !hasSelectedValue) {
                // Restore button states
                createButtons.forEach(button => {
                    if (button && button.dataset.originalContent) {
                        button.innerHTML = button.dataset.originalContent;
                        button.disabled = false;
                        button.classList.remove('opacity-50', 'cursor-not-allowed');
                    }
                });
                showProjectToast('Please select a client before creating the project.', 'error');
                return false;
            }
            
            // If we have selectedClient but not selectedValue, update the select element
            if (hasSelectedClient && !hasSelectedValue) {
                console.log('Updating select element value to:', window.selectedClient.id);
                clientSelect.value = window.selectedClient.id;
            }
        }
        
        // Show creating overlay
        const creatingOverlay = document.createElement('div');
        creatingOverlay.id = 'creating-overlay';
        creatingOverlay.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        creatingOverlay.innerHTML = `
            <div class="bg-white rounded-lg p-8 max-w-sm w-full mx-4 text-center">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <h3 class="text-lg font-semibold text-gray-900 mb-2">Creating Project</h3>
                <p class="text-gray-600">Please wait while we process your project...</p>
            </div>
        `;
        document.body.appendChild(creatingOverlay);
        
        // Submit the form
        const form = document.querySelector('form');
        if (form) {
            console.log('Submitting form...');
            
            // Debug: Check form data before submission
            const formData = new FormData(form);
            console.log('Form data before submission:');
            for (let [key, value] of formData.entries()) {
                console.log(`  ${key}: ${value}`);
            }
            
            // Ensure client field is included
            if (window.selectedClient && window.selectedClient.id) {
                console.log('Adding client field to form:', window.selectedClient.id);
                // Create a hidden input to ensure the client field is included
                const hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = 'client';
                hiddenInput.value = window.selectedClient.id;
                form.appendChild(hiddenInput);
            }
            
            form.submit();
        }
    };
});