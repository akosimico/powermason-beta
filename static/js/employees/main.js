// static/js/employees/main.js
/**
 * Employee Management JavaScript
 * Production-ready with proper error handling and UX
 */
class EmployeeManager {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.initializeModals();
        this.initializeTooltips();
    }

    bindEvents() {
        // Add Employee modal buttons - use event delegation for dynamically added buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="show-add-employee"]') || 
                e.target.closest('[data-action="show-add-employee"]')) {
                e.preventDefault();
                this.showAddEmployeeModal();
            }
        });

        // Also bind to existing buttons on page load
        document.querySelectorAll('[data-action="show-add-employee"]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.showAddEmployeeModal();
            });
        });

        // Modal click outside to close
        document.addEventListener('click', (e) => {
            if (e.target.id === 'addEmployeeModal') {
                this.closeModal('addEmployeeModal');
            }
        });

        // Contract extension buttons
        document.querySelectorAll('.extend-contract-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.openExtendContractModal(e));
        });

        // Employee status toggle buttons
        document.querySelectorAll('.deactivate-employee-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const employeeId = btn.getAttribute('data-employee-id');
                this.toggleEmployeeStatus(employeeId, 'inactive');
            });
        });

        document.querySelectorAll('.activate-employee-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const employeeId = btn.getAttribute('data-employee-id');
                this.toggleEmployeeStatus(employeeId, 'active');
            });
        });

        // Modal close buttons
        document.getElementById('closeModal')?.addEventListener('click', () => {
            this.closeModal('extendContractModal');
        });

        document.getElementById('cancelExtend')?.addEventListener('click', () => {
            this.closeModal('extendContractModal');
        });

        // Form submission
        document.getElementById('extendContractForm')?.addEventListener('submit', (e) => {
            this.handleContractExtension(e);
        });

        // Search form auto-submit with debounce
        const searchInput = document.querySelector('input[name="search"]');
        if (searchInput) {
            let debounceTimer;
            searchInput.addEventListener('input', () => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    if (searchInput.value.length > 2 || searchInput.value.length === 0) {
                        searchInput.closest('form').submit();
                    }
                }, 500);
            });
        }

        // ESC key to close modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });

        // Click outside modal to close
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('bg-opacity-50')) {
                this.closeAllModals();
            }
        });
    }

    showAddEmployeeModal() {
        console.log('showAddEmployeeModal called'); // Debug log
        const createUrl = document.querySelector('[data-create-url]')?.dataset.createUrl || '/employees/create/';
        window.location.href = createUrl;
    }

    createAddEmployeeModal() {
        console.log('createAddEmployeeModal called'); // Debug log
        // Get the create URL from the page
        const createUrlElement = document.querySelector('[data-create-url]');
        const createUrl = createUrlElement ? createUrlElement.dataset.createUrl : '/employees/create/';
        
        const modalHTML = `
        <div id="addEmployeeModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full hidden z-50">
            <div class="relative top-10 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-xl bg-white">
                <div class="mt-3">
                    <div class="flex items-center justify-between mb-6">
                        <h3 class="text-xl font-semibold text-gray-900 flex items-center">
                            <svg class="w-6 h-6 mr-3 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M8 9a3 3 0 100-6 3 3 0 000 6zM8 11a6 6 0 016 6H2a6 6 0 016-6zM16 7a1 1 0 10-2 0v1h-1a1 1 0 100 2h1v1a1 1 0 102 0v-1h1a1 1 0 100-2h-1V7z"/>
                            </svg>
                            Add New Employee
                        </h3>
                        <button type="button" class="text-gray-400 hover:text-gray-600 transition-colors" onclick="window.employeeManager.closeModal('addEmployeeModal')">
                            <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                            </svg>
                        </button>
                    </div>
                    
                    <form id="addEmployeeForm" action="${createUrl}" method="post" class="space-y-6">
                        ${document.querySelector('[name=csrfmiddlewaretoken]') ? document.querySelector('[name=csrfmiddlewaretoken]').outerHTML : ''}
                        
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div class="space-y-4">
                                <h4 class="text-lg font-medium text-gray-900">Personal Information</h4>
                                
                                <div>
                                    <label for="modal_first_name" class="block text-sm font-medium text-gray-700 mb-1">First Name *</label>
                                    <input type="text" name="first_name" id="modal_first_name" required 
                                           class="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500">
                                </div>
                                
                                <div>
                                    <label for="modal_last_name" class="block text-sm font-medium text-gray-700 mb-1">Last Name *</label>
                                    <input type="text" name="last_name" id="modal_last_name" required 
                                           class="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500">
                                </div>
                                
                                <div>
                                    <label for="modal_email" class="block text-sm font-medium text-gray-700 mb-1">Email</label>
                                    <input type="email" name="email" id="modal_email" 
                                           class="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500">
                                </div>
                            </div>

                            <div class="space-y-4">
                                <h4 class="text-lg font-medium text-gray-900">Employment Details</h4>
                                
                                <div>
                                    <label for="modal_role" class="block text-sm font-medium text-gray-700 mb-1">Role *</label>
                                    <select name="role" id="modal_role" required 
                                            class="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500">
                                        <option value="">Select a role</option>
                                        <option value="DEV">Developer</option>
                                        <option value="PM">Project Manager</option>
                                        <option value="DES">Designer</option>
                                        <option value="QA">QA Engineer</option>
                                        <option value="LB">Labor</option>
                                        <option value="OTHER">Other</option>
                                    </select>
                                </div>
                                
                                <div>
                                    <label for="modal_hire_date" class="block text-sm font-medium text-gray-700 mb-1">Hire Date *</label>
                                    <input type="date" name="hire_date" id="modal_hire_date" required 
                                           class="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500">
                                </div>
                                
                                <div>
                                    <label for="modal_contract_end_date" class="block text-sm font-medium text-gray-700 mb-1">Contract End Date</label>
                                    <input type="date" name="contract_end_date" id="modal_contract_end_date" 
                                           class="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500">
                                </div>
                            </div>
                        </div>

                        <div class="flex justify-end space-x-3 pt-6 border-t border-gray-200">
                            <button type="button" onclick="window.employeeManager.closeModal('addEmployeeModal')"
                                    class="px-6 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors">
                                Cancel
                            </button>
                            <button type="submit" 
                                    class="px-6 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 transition-colors">
                                Add Employee
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>`;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Bind form submission
        document.getElementById('addEmployeeForm').addEventListener('submit', (e) => {
            this.handleAddEmployeeSubmission(e);
        });
        
        this.showModal('addEmployeeModal');
        this.setDefaultDates();
    }

    setDefaultDates() {
        const today = new Date().toISOString().split('T')[0];
        const hireDateField = document.getElementById('modal_hire_date');
        const contractEndField = document.getElementById('modal_contract_end_date');
        
        if (hireDateField && !hireDateField.value) {
            hireDateField.value = today;
        }
        
        // Set contract end date to 1 year from hire date
        if (contractEndField && !contractEndField.value) {
            const oneYearLater = new Date();
            oneYearLater.setFullYear(oneYearLater.getFullYear() + 1);
            contractEndField.value = oneYearLater.toISOString().split('T')[0];
        }
    }

    async handleAddEmployeeSubmission(event) {
        event.preventDefault();
        
        const form = event.target;
        const submitButton = form.querySelector('button[type="submit"]');
        const originalText = submitButton.innerHTML;
        
        // Show loading state
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Adding...';
        submitButton.disabled = true;
        
        try {
            const formData = new FormData(form);
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (response.ok) {
                this.showNotification('Employee added successfully!', 'success');
                this.closeModal('addEmployeeModal');
                
                // Reload page to show new employee
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                // Handle validation errors
                const text = await response.text();
                console.error('Form submission error:', text);
                this.showNotification('Failed to add employee. Please check the form for errors.', 'error');
            }
        } catch (error) {
            console.error('Error adding employee:', error);
            this.showNotification('An error occurred while adding the employee', 'error');
        } finally {
            submitButton.innerHTML = originalText;
            submitButton.disabled = false;
        }
    }

    initializeModals() {
        // Set minimum date for contract extension to today
        const today = new Date().toISOString().split('T')[0];
        const newEndDateInput = document.getElementById('newEndDate');
        if (newEndDateInput) {
            newEndDateInput.setAttribute('min', today);
        }
    }

    initializeTooltips() {
        // Add hover effects and tooltips for better UX
        document.querySelectorAll('[title]').forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                this.showTooltip(e.target, e.target.getAttribute('title'));
            });
            element.addEventListener('mouseleave', () => {
                this.hideTooltip();
            });
        });
    }

    openExtendContractModal(event) {
        const button = event.currentTarget;
        const employeeId = button.getAttribute('data-employee-id');
        const employeeName = button.getAttribute('data-employee-name');

        if (!employeeId || !employeeName) {
            this.showNotification('Error: Missing employee information', 'error');
            return;
        }

        // Populate modal
        document.getElementById('employeeName').value = employeeName;
        
        // Set default date (1 year from today)
        const oneYearFromNow = new Date();
        oneYearFromNow.setFullYear(oneYearFromNow.getFullYear() + 1);
        document.getElementById('newEndDate').value = oneYearFromNow.toISOString().split('T')[0];

        // Store employee ID for form submission
        const form = document.getElementById('extendContractForm');
        form.setAttribute('data-employee-id', employeeId);

        // Show modal with animation
        this.showModal('extendContractModal');
    }

    async handleContractExtension(event) {
        event.preventDefault();
        
        const form = event.target;
        const employeeId = form.getAttribute('data-employee-id');
        const newEndDate = document.getElementById('newEndDate').value;
        const submitButton = form.querySelector('button[type="submit"]');

        if (!newEndDate) {
            this.showNotification('Please select a new contract end date', 'error');
            return;
        }

        // Validate date is in the future
        const selectedDate = new Date(newEndDate);
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        if (selectedDate <= today) {
            this.showNotification('Contract end date must be in the future', 'error');
            return;
        }

        // Show loading state
        const originalButtonText = submitButton.innerHTML;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Extending...';
        submitButton.disabled = true;

        try {
            const response = await fetch(`/employees/${employeeId}/extend-contract/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: `new_end_date=${newEndDate}`
            });

            const data = await response.json();

            if (response.ok && data.success) {
                this.showNotification(data.message || 'Contract extended successfully', 'success');
                this.closeModal('extendContractModal');
                
                // Refresh the page after a short delay to show the notification
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                throw new Error(data.error || 'Failed to extend contract');
            }
        } catch (error) {
            console.error('Contract extension error:', error);
            this.showNotification(error.message || 'An error occurred while extending the contract', 'error');
        } finally {
            // Reset button state
            submitButton.innerHTML = originalButtonText;
            submitButton.disabled = false;
        }
    }

    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('hidden');
            // Add animation
            setTimeout(() => {
                modal.querySelector('.relative').classList.add('animate-fade-in');
            }, 10);
            
            // Focus management for accessibility
            const firstInput = modal.querySelector('input, button, select, textarea');
            if (firstInput) {
                firstInput.focus();
            }
        }
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
            modal.querySelector('.relative')?.classList.remove('animate-fade-in');
            
            // Reset form if it exists
            const form = modal.querySelector('form');
            if (form) {
                form.reset();
                form.removeAttribute('data-employee-id');
            }
        }
    }

    closeAllModals() {
        document.querySelectorAll('[id$="Modal"]').forEach(modal => {
            if (!modal.classList.contains('hidden')) {
                this.closeModal(modal.id);
            }
        });
    }

    showNotification(message, type = 'info', duration = 5000) {
        // Remove existing notifications
        const existingNotifications = document.querySelectorAll('.notification-toast');
        existingNotifications.forEach(n => n.remove());

        const notification = document.createElement('div');
        notification.className = `notification-toast fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transform transition-all duration-300 translate-x-full`;
        
        const typeClasses = {
            success: 'bg-green-500 text-white',
            error: 'bg-red-500 text-white',
            warning: 'bg-yellow-500 text-white',
            info: 'bg-blue-500 text-white'
        };

        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };

        notification.className += ` ${typeClasses[type] || typeClasses.info}`;
        notification.innerHTML = `
            <div class="flex items-center space-x-2">
                <i class="${icons[type] || icons.info}"></i>
                <span>${message}</span>
                <button class="ml-4 text-white hover:text-gray-200 focus:outline-none" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 10);

        // Auto-remove after duration
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }

    showTooltip(element, text) {
        this.hideTooltip(); // Remove any existing tooltip

        const tooltip = document.createElement('div');
        tooltip.id = 'tooltip';
        tooltip.className = 'absolute z-50 px-2 py-1 text-xs text-white bg-gray-800 rounded shadow-lg pointer-events-none';
        tooltip.textContent = text;

        document.body.appendChild(tooltip);

        const rect = element.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();

        tooltip.style.left = `${rect.left + (rect.width / 2) - (tooltipRect.width / 2)}px`;
        tooltip.style.top = `${rect.top - tooltipRect.height - 5}px`;
    }

    hideTooltip() {
        const existingTooltip = document.getElementById('tooltip');
        if (existingTooltip) {
            existingTooltip.remove();
        }
    }

    getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }

    // Utility method for formatting dates
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    // Method to handle status changes
    async toggleEmployeeStatus(employeeId, newStatus) {

        try {
            const response = await fetch(`/employees/${employeeId}/toggle-status/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                // Log the response for debugging
                const responseText = await response.text();
                console.error('HTTP Error:', response.status, responseText);
                throw new Error(`HTTP ${response.status}: Failed to change status`);
            }

            const data = await response.json();

            if (data.success) {
                this.showNotification(`Employee ${newStatus === 'active' ? 'activated' : 'deactivated'} successfully`, 'success');
                setTimeout(() => window.location.reload(), 1000);
            } else {
                throw new Error(data.error || 'Failed to change status');
            }
        } catch (error) {
            console.error('Status change error:', error);

            // Show more specific error message
            let errorMessage = 'Failed to change employee status';
            if (error.message.includes('Unexpected token')) {
                errorMessage = 'Server returned an unexpected response. Please check the console for details.';
            } else if (error.message) {
                errorMessage = error.message;
            }

            this.showNotification(errorMessage, 'error');
        }
    }

    // Method to handle bulk actions (for future implementation)
    handleBulkAction(action, selectedIds) {
        if (!selectedIds.length) {
            this.showNotification('Please select employees first', 'warning');
            return;
        }

        const confirmMessage = `Are you sure you want to ${action} ${selectedIds.length} employee(s)?`;
        if (!confirm(confirmMessage)) {
            return;
        }

        // Implementation would depend on specific bulk actions needed
        console.log(`Bulk ${action} for employees:`, selectedIds);
    }
}

// Enhanced search functionality
class EmployeeSearch {
    constructor() {
        this.searchInput = document.querySelector('input[name="search"]');
        this.init();
    }

    init() {
        if (!this.searchInput) return;

        this.addSearchEnhancements();
    }

    addSearchEnhancements() {
        // Add search icon and clear button
        const searchContainer = this.searchInput.parentElement;
        searchContainer.classList.add('relative');

        // Search icon
        const searchIcon = document.createElement('div');
        searchIcon.className = 'absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400';
        searchIcon.innerHTML = '<i class="fas fa-search"></i>';
        searchContainer.insertBefore(searchIcon, this.searchInput);

        // Adjust input padding for icon
        this.searchInput.classList.add('pl-10');

        // Clear button (shows when there's text)
        const clearButton = document.createElement('button');
        clearButton.type = 'button';
        clearButton.className = 'absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 hidden';
        clearButton.innerHTML = '<i class="fas fa-times"></i>';
        searchContainer.appendChild(clearButton);

        // Show/hide clear button based on input content
        this.searchInput.addEventListener('input', () => {
            if (this.searchInput.value.trim()) {
                clearButton.classList.remove('hidden');
            } else {
                clearButton.classList.add('hidden');
            }
        });

        // Clear button functionality
        clearButton.addEventListener('click', () => {
            this.searchInput.value = '';
            clearButton.classList.add('hidden');
            this.searchInput.focus();
            // Trigger search
            this.searchInput.closest('form').submit();
        });

        // Initial state
        if (this.searchInput.value.trim()) {
            clearButton.classList.remove('hidden');
        }
    }
}

// Loading states handler
class LoadingHandler {
    static show(element, text = 'Loading...') {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (!element) return;

        const originalContent = element.innerHTML;
        element.setAttribute('data-original-content', originalContent);
        element.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i>${text}`;
        element.disabled = true;
    }

    static hide(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (!element) return;

        const originalContent = element.getAttribute('data-original-content');
        if (originalContent) {
            element.innerHTML = originalContent;
            element.removeAttribute('data-original-content');
        }
        element.disabled = false;
    }
}

// Initialize immediately when script loads
window.employeeManager = new EmployeeManager();
window.employeeSearch = new EmployeeSearch();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Add custom CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeIn {
            from { opacity: 0; transform: scale(0.95); }
            to { opacity: 1; transform: scale(1); }
        }
        
        .animate-fade-in {
            animation: fadeIn 0.2s ease-out;
        }
        
        .notification-toast {
            max-width: 400px;
            word-wrap: break-word;
        }
        
        /* Custom scrollbar for tables */
        .overflow-x-auto::-webkit-scrollbar {
            height: 8px;
        }
        
        .overflow-x-auto::-webkit-scrollbar-track {
            background: #f1f5f9;
        }
        
        .overflow-x-auto::-webkit-scrollbar-thumb {
            background: #cbd5e1;
            border-radius: 4px;
        }
        
        .overflow-x-auto::-webkit-scrollbar-thumb:hover {
            background: #94a3b8;
        }

        /* Improved focus styles for accessibility */
        button:focus, input:focus, select:focus {
            outline: 2px solid #3b82f6;
            outline-offset: 2px;
        }

        /* Loading animation */
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        .fa-spin {
            animation: spin 1s linear infinite;
        }
    `;
    document.head.appendChild(style);

    // Add keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + K to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[name="search"]');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }

        // Ctrl/Cmd + N to show add employee modal
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            if (window.employeeManager) {
                window.employeeManager.showAddEmployeeModal();
            }
        }
    });

    // Add helpful keyboard shortcut hints
    const addKeyboardHints = () => {
        const searchInput = document.querySelector('input[name="search"]');
        if (searchInput) {
            searchInput.setAttribute('placeholder', 
                searchInput.getAttribute('placeholder') + ' (Ctrl+K)'
            );
        }
    };

    addKeyboardHints();
});

// Export for use in other scripts
window.EmployeeManager = EmployeeManager;
window.EmployeeSearch = EmployeeSearch;
window.LoadingHandler = LoadingHandler;