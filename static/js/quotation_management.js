/**
 * Quotation Management JavaScript
 * 
 * Handles quotation upload, approval, deletion, and RFS download functionality
 */

// Global variables
let currentProjectId = null;
let quotations = [];

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get project ID from URL - try multiple patterns
    const pathParts = window.location.pathname.split('/');
    console.log('URL path parts:', pathParts);
    
    // Try different URL patterns
    if (pathParts.includes('pending') && pathParts.includes('review')) {
        // URL: /projects/pending/{id}/review/
        const pendingIndex = pathParts.indexOf('pending');
        currentProjectId = pathParts[pendingIndex + 1];
    } else if (pathParts.includes('review')) {
        // URL: /projects/{id}/review/
        const reviewIndex = pathParts.indexOf('review');
        currentProjectId = pathParts[reviewIndex - 1];
    } else {
        // Fallback: assume it's the second to last part
        currentProjectId = pathParts[pathParts.length - 2];
    }
    
    // Validate project ID is a number
    if (!currentProjectId || isNaN(currentProjectId)) {
        console.error('Invalid project ID extracted:', currentProjectId);
        return;
    }
    
    console.log('Extracted project ID:', currentProjectId);
    
    // Initialize event listeners
    initializeEventListeners();
    
    // Load initial quotations
    loadQuotations();
    
    // Check for auto-download
    checkForAutoDownload();
});

/**
 * Initialize all event listeners
 */
function initializeEventListeners() {
    // Upload quotation button
    const uploadBtn = document.getElementById('uploadQuotationBtn');
    console.log('Upload button found:', !!uploadBtn);
    if (uploadBtn) {
        uploadBtn.addEventListener('click', function(e) {
            console.log('Upload button clicked!');
            e.preventDefault();
            openUploadModal();
        });
        console.log('Upload button event listener attached');
    } else {
        console.error('Upload button not found!');
    }
    
    // Upload form submission
    const uploadForm = document.getElementById('quotationUploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleQuotationUpload);
    }
    
    // File input change for auto-calculation and file display
    const fileInput = document.getElementById('quotation_file');
    console.log('File input element found:', !!fileInput);
    if (fileInput) {
        fileInput.addEventListener('change', handleFileChange);
        console.log('File change event listener attached');
    } else {
        console.error('File input element not found!');
    }
    
    // Remove file button
    const removeFileBtn = document.getElementById('remove-file');
    if (removeFileBtn) {
        removeFileBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Remove file button clicked (initial setup)');
            removeSelectedFile();
        });
    }
}

/**
 * Open upload quotation modal
 */
function openUploadModal() {
    console.log('openUploadModal called');
    const modal = document.getElementById('uploadQuotationModal');
    console.log('Modal element found:', !!modal);
    
    if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        console.log('Modal shown');
        
        // Re-initialize file input event listeners when modal opens
        // This ensures the elements are accessible
        const fileInput = document.getElementById('quotation_file');
        const removeFileBtn = document.getElementById('remove-file');
        const fileSelected = document.getElementById('file-selected');
        const fileName = document.getElementById('file-name');
        
        console.log('Modal opened, re-initializing file input listeners');
        console.log('File input found:', !!fileInput);
        console.log('Remove file button found:', !!removeFileBtn);
        console.log('File selected element found:', !!fileSelected);
        console.log('File name element found:', !!fileName);
        
        if (fileInput) {
            // Remove any existing listeners to avoid duplicates
            fileInput.removeEventListener('change', handleFileChange);
            // Add the listener again
            fileInput.addEventListener('change', handleFileChange);
            console.log('File change event listener re-attached');
            
            // Test if the event listener is working by triggering a test
            console.log('File input value:', fileInput.value);
            
            // Add a simple test event listener to see if it works
            fileInput.addEventListener('change', function(e) {
                console.log('DIRECT TEST: File input changed!', e.target.files);
            });
        } else {
            console.error('File input element not found in modal!');
        }
        
        if (removeFileBtn) {
            // Remove any existing listeners to avoid duplicates
            removeFileBtn.removeEventListener('click', removeSelectedFile);
            // Add the listener again
            removeFileBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('Remove file button clicked');
                removeSelectedFile();
            });
            console.log('Remove file button event listener re-attached');
        } else {
            console.error('Remove file button element not found in modal!');
        }
    } else {
        console.error('Upload modal element not found!');
    }
}

/**
 * Close upload quotation modal
 */
function closeUploadModal() {
    const modal = document.getElementById('uploadQuotationModal');
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
        
        // Reset form
        const form = document.getElementById('quotationUploadForm');
        if (form) {
            form.reset();
        }
        
        // Reset button state
        const submitBtn = document.getElementById('uploadSubmitBtn');
        if (submitBtn) {
            // Reset button text to original
            const btnText = document.getElementById('uploadBtnText');
            const btnLoading = document.getElementById('uploadBtnLoading');
            
            if (btnText && btnLoading) {
                btnText.classList.remove('hidden');
                btnLoading.classList.add('hidden');
            }
            
            // Reset button state
            submitBtn.disabled = false;
            submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }
        
        // Reset file selection state
        const fileSelected = document.getElementById('file-selected');
        if (fileSelected) {
            fileSelected.classList.add('hidden');
        }
        
        // Reset file input
        const fileInput = document.getElementById('quotation_file');
        if (fileInput) {
            fileInput.value = '';
        }
        
        // Reset total amount input
        const totalAmountInput = document.getElementById('total_amount');
        if (totalAmountInput) {
            totalAmountInput.disabled = false;
            totalAmountInput.placeholder = '0.00';
        }
    }
}

/**
 * Handle file input change for auto-calculation and file display
 */
function handleFileChange(event) {
    console.log('handleFileChange called', event.target.files);
    const file = event.target.files[0];
    const totalAmountInput = document.getElementById('total_amount');
    const fileSelected = document.getElementById('file-selected');
    const fileName = document.getElementById('file-name');
    const removeFileBtn = document.getElementById('remove-file');
    
    console.log('File elements found:', {
        totalAmountInput: !!totalAmountInput,
        fileSelected: !!fileSelected,
        fileName: !!fileName,
        removeFileBtn: !!removeFileBtn
    });
    
    if (file) {
        console.log('File selected:', file.name);
        // Show file selected indicator
        if (fileName) {
            fileName.textContent = file.name;
            console.log('File name updated:', file.name);
        }
        if (fileSelected) {
            fileSelected.classList.remove('hidden');
            console.log('File selected indicator shown');
        }
        
        // Handle auto-calculation for Excel files
        if (file.name.toLowerCase().endsWith('.xlsx') || file.name.toLowerCase().endsWith('.xls')) {
            // Show message that amount will be auto-calculated
            if (totalAmountInput) {
                totalAmountInput.placeholder = 'Will be auto-calculated from Excel file';
                totalAmountInput.disabled = true;
            }
        } else {
            if (totalAmountInput) {
                totalAmountInput.placeholder = '0.00';
                totalAmountInput.disabled = false;
            }
        }
    } else {
        console.log('No file selected');
        // Hide file selected indicator
        if (fileSelected) {
            fileSelected.classList.add('hidden');
        }
        if (totalAmountInput) {
            totalAmountInput.placeholder = '0.00';
            totalAmountInput.disabled = false;
        }
    }
}

/**
 * Remove selected file
 */
function removeSelectedFile() {
    console.log('removeSelectedFile called');
    const fileInput = document.getElementById('quotation_file');
    const fileSelected = document.getElementById('file-selected');
    const fileName = document.getElementById('file-name');
    const totalAmountInput = document.getElementById('total_amount');
    
    console.log('Remove file elements found:', {
        fileInput: !!fileInput,
        fileSelected: !!fileSelected,
        fileName: !!fileName,
        totalAmountInput: !!totalAmountInput
    });
    
    if (fileInput) {
        fileInput.value = '';
        console.log('File input cleared');
    }
    if (fileSelected) {
        fileSelected.classList.add('hidden');
        console.log('File selected indicator hidden');
    }
    if (fileName) {
        fileName.textContent = '';
        console.log('File name cleared');
    }
    if (totalAmountInput) {
        totalAmountInput.placeholder = '0.00';
        totalAmountInput.disabled = false;
        totalAmountInput.value = '';
        console.log('Total amount input reset');
    }
    
    // Show success message
    console.log('File removal completed successfully');
}

/**
 * Handle quotation upload form submission
 */
async function handleQuotationUpload(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    // Show loading state
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Uploading...';
    submitBtn.disabled = true;
    
    try {
        const response = await fetch(`/projects/${currentProjectId}/quotations/upload/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Quotation uploaded successfully!', 'success');
            closeUploadModal();
            loadQuotations(); // Refresh quotations list
            // Update budget field after quotations change
            if (typeof updateBudgetFromQuotations === 'function') {
                updateBudgetFromQuotations();
            }
        } else {
            showNotification(data.error || 'Failed to upload quotation', 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showNotification('An error occurred while uploading the quotation', 'error');
    } finally {
        // Reset button state
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
}

/**
 * Load quotations for the current project
 */
async function loadQuotations() {
    try {
        const response = await fetch(`/projects/${currentProjectId}/quotations/list/`);
        const data = await response.json();
        
        if (data.success) {
            quotations = data.quotations;
            updateQuotationDisplay();
            updateApprovalButton();
        } else {
            console.error('Failed to load quotations:', data.error);
        }
    } catch (error) {
        console.error('Error loading quotations:', error);
    }
}

/**
 * Update quotation display in the table
 */
function updateQuotationDisplay() {
    console.log('updateQuotationDisplay called with', quotations.length, 'quotations');
    
    // Update quotation count display
    updateQuotationCount();
    
    // Find the quotation table body
    const quotationSection = document.querySelector('#quotation-management-section');
    if (!quotationSection) {
        console.log('Quotation section not found');
        return;
    }
    
    let tableBody = quotationSection.querySelector('tbody');
    if (!tableBody) {
        console.log('No tbody element found in quotation section');
        console.log('Available elements in quotation section:', quotationSection.querySelectorAll('*'));
        return;
    }
    
    // Clear existing rows
    tableBody.innerHTML = '';
    
    if (quotations.length === 0) {
        // Show empty state - check if empty state row already exists
        let emptyRow = document.getElementById('empty-state-row');
        if (!emptyRow) {
            emptyRow = document.createElement('tr');
            emptyRow.id = 'empty-state-row';
            emptyRow.innerHTML = `
                <td colspan="5" class="px-4 py-8 text-center">
                    <div class="text-center py-8">
                        <svg class="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                        </svg>
                        <p class="text-gray-500 text-sm">No quotations uploaded yet</p>
                        <p class="text-gray-400 text-xs mt-1">Upload supplier quotations to compare and select the best one</p>
                    </div>
                </td>
            `;
            tableBody.appendChild(emptyRow);
        }
        return;
    }
    
    // Add quotation rows
    quotations.forEach(quotation => {
        const row = document.createElement('tr');
        row.className = quotation.status === 'APPROVED' ? 'bg-green-50' : quotation.status === 'REJECTED' ? 'bg-red-50' : '';
        row.setAttribute('data-quotation-id', quotation.id);
        
        const statusBadge = quotation.status === 'APPROVED' 
            ? '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"><svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path></svg>Approved</span>'
            : quotation.status === 'REJECTED'
            ? '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"><svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path></svg>Rejected</span>'
            : '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800"><svg class="w-3 h-3 mr-1 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>Pending</span>';
        
        const actions = quotation.status === 'PENDING'
            ? `<div class="flex items-center space-x-2">
                 <a href="${quotation.quotation_file?.url || '#'}" target="_blank" class="inline-flex items-center px-2 py-1 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-md transition-colors">
                   <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>View
                 </a>
                 <button data-quotation-id="${quotation.id}" onclick="approveQuotation(this.getAttribute('data-quotation-id'))" class="inline-flex items-center px-2 py-1 text-xs font-medium text-green-600 bg-green-50 hover:bg-green-100 rounded-md transition-colors">
                   <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>Approve
                 </button>
                 <button data-quotation-id="${quotation.id}" onclick="deleteQuotation(this.getAttribute('data-quotation-id'))" class="inline-flex items-center px-2 py-1 text-xs font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-md transition-colors">
                   <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>Delete
                 </button>
               </div>`
            : `<div class="flex items-center space-x-2">
                 <a href="${quotation.quotation_file?.url || '#'}" target="_blank" class="inline-flex items-center px-2 py-1 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-md transition-colors">
                   <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>View
                 </a>
               </div>`;
        
        row.innerHTML = `
            <td class="px-4 py-4">
                <div class="text-sm font-medium text-gray-900">${quotation.supplier_name || 'Unknown'}</div>
                <div class="text-xs text-gray-500 truncate max-w-xs" title="${quotation.quotation_file?.name || 'No file'}">
                    ${quotation.quotation_file?.name || 'No file'}
                </div>
            </td>
            <td class="px-4 py-4">
                <div class="text-sm font-semibold text-gray-900">₱${quotation.total_amount ? parseFloat(quotation.total_amount).toLocaleString('en-PH', {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '0.00'}</div>
            </td>
            <td class="px-4 py-4 text-sm text-gray-500">
                ${quotation.date_submitted ? new Date(quotation.date_submitted).toLocaleDateString('en-US', {month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true}) : 'Unknown'}
            </td>
            <td class="px-4 py-4">
                ${statusBadge}
            </td>
            <td class="px-4 py-4">
                ${actions}
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    console.log('Updated quotation table with', quotations.length, 'quotations');
}

/**
 * Update quotation count display
 */
function updateQuotationCount() {
    const countDisplay = document.querySelector('#quotation-management-section .text-sm.text-gray-500');
    if (countDisplay) {
        countDisplay.textContent = `${quotations.length}/5 quotations`;
        console.log('Updated quotation count display to:', countDisplay.textContent);
    } else {
        console.log('Quotation count display element not found');
    }
}

/**
 * Update approval button state based on quotations
 */
function updateApprovalButton() {
    const approveBtn = document.getElementById('approve-budget-btn');
    const hasApproved = quotations.some(q => q.status === 'APPROVED');
    
    if (approveBtn) {
        if (hasApproved) {
            approveBtn.disabled = false;
            approveBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        } else {
            approveBtn.disabled = true;
            approveBtn.classList.add('opacity-50', 'cursor-not-allowed');
        }
    }
}

/**
 * Approve a quotation
 */
async function approveQuotation(quotationId) {
    if (!confirm('Are you sure you want to approve this quotation? This will reject all other pending quotations.')) {
        return;
    }
    
    try {
        const response = await fetch(`/projects/${currentProjectId}/quotations/${quotationId}/approve/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(data.message, 'success');
            loadQuotations(); // Refresh quotations list
            // Update budget field after quotation approval
            console.log('Approval response data:', data);
            console.log('Quotation data:', data.quotation);
            console.log('Total amount:', data.quotation.total_amount);
            console.log('Calling updateApprovedBudgetField with:', data.quotation.total_amount);
            
            // Try the template function first
            if (typeof window.updateApprovedBudgetField === 'function') {
                window.updateApprovedBudgetField(data.quotation.total_amount);
            }
            
            // Also try the quotation management function
            updateBudgetFieldAfterApproval(data.quotation);
        } else {
            showNotification(data.error || 'Failed to approve quotation', 'error');
        }
    } catch (error) {
        console.error('Approval error:', error);
        showNotification('An error occurred while approving the quotation', 'error');
    }
}

/**
 * Update budget field after quotation approval
 */
function updateBudgetFieldAfterApproval(quotationData) {
    console.log('DEBUG: updateBudgetFieldAfterApproval called with:', quotationData);
    
    if (!quotationData || !quotationData.total_amount) {
        console.log('DEBUG: No quotation data or total_amount available');
        return;
    }
    
    // Get the budget input fields
    const budgetInput = document.getElementById('approved_budget');
    const hiddenInput = document.getElementById('approved_budget_hidden');
    
    console.log('DEBUG: Budget input found:', !!budgetInput);
    console.log('DEBUG: Hidden input found:', !!hiddenInput);
    console.log('DEBUG: Budget input current value:', budgetInput ? budgetInput.value : 'N/A');
    console.log('DEBUG: Hidden input current value:', hiddenInput ? hiddenInput.value : 'N/A');
    
    if (!budgetInput || !hiddenInput) {
        console.log('DEBUG: Budget input fields not found');
        console.log('DEBUG: Available elements with approved_budget in ID:', document.querySelectorAll('[id*="approved_budget"]'));
        return;
    }
    
    // Update both fields with the approved quotation amount
    const approvedAmount = parseFloat(quotationData.total_amount);
    const formattedAmount = approvedAmount.toFixed(2);
    
    console.log('DEBUG: Approved amount:', approvedAmount);
    console.log('DEBUG: Formatted amount:', formattedAmount);
    
    // Check if the budget input is disabled/readonly
    console.log('DEBUG: Budget input disabled:', budgetInput.disabled);
    console.log('DEBUG: Budget input readonly:', budgetInput.readOnly);
    
    // Temporarily enable the field to update its value
    const wasDisabled = budgetInput.disabled;
    const wasReadOnly = budgetInput.readOnly;
    
    if (wasDisabled) {
        budgetInput.disabled = false;
    }
    if (wasReadOnly) {
        budgetInput.readOnly = false;
    }
    
    // Update the values
    budgetInput.value = formattedAmount;
    hiddenInput.value = formattedAmount;
    
    // Re-disable the field to maintain read-only behavior
    if (wasDisabled) {
        budgetInput.disabled = true;
    }
    if (wasReadOnly) {
        budgetInput.readOnly = true;
    }
    
    // Force trigger change events
    budgetInput.dispatchEvent(new Event('change', { bubbles: true }));
    budgetInput.dispatchEvent(new Event('input', { bubbles: true }));
    hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
    
    console.log('DEBUG: Updated budget fields to:', formattedAmount);
    console.log('DEBUG: Budget input value after update:', budgetInput.value);
    console.log('DEBUG: Hidden input value after update:', hiddenInput.value);
    
    // Verify the update worked
    if (budgetInput.value !== formattedAmount) {
        console.warn('DEBUG: Budget input value did not update correctly, retrying...');
        setTimeout(() => {
            budgetInput.value = formattedAmount;
            hiddenInput.value = formattedAmount;
            console.log('DEBUG: Retry - Budget input value:', budgetInput.value);
        }, 100);
    }
    
    // Also update the budget info text to show the new amount
    updateBudgetInfoText(approvedAmount);
    
    // Fallback: Try using the global function if available
    if (typeof window.updateBudgetField === 'function') {
        console.log('DEBUG: Trying fallback updateBudgetField function');
        window.updateBudgetField(approvedAmount);
    }
}

/**
 * Update budget info text to reflect the approved amount
 */
function updateBudgetInfoText(approvedAmount) {
    const budgetInfo = document.querySelector('.mt-1.text-xs.text-gray-500.space-y-1');
    if (budgetInfo) {
        const estimatedCostText = budgetInfo.querySelector('p');
        if (estimatedCostText) {
            // Get the estimated cost from the current text or use a default
            const currentText = estimatedCostText.textContent;
            const estimatedCostMatch = currentText.match(/Estimated Cost: ₱([\d,]+\.?\d*)/);
            const estimatedCost = estimatedCostMatch ? parseFloat(estimatedCostMatch[1].replace(/,/g, '')) : 0;
            
            estimatedCostText.innerHTML = `Estimated Cost: ₱${estimatedCost.toLocaleString('en-PH', {minimumFractionDigits: 2})} <span class="text-green-600">(Budget: ₱${approvedAmount.toLocaleString('en-PH', {minimumFractionDigits: 2})})</span>`;
        }
    }
}

/**
 * Delete a quotation
 */
async function deleteQuotation(quotationId) {
    if (!confirm('Are you sure you want to delete this quotation? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/projects/${currentProjectId}/quotations/${quotationId}/delete/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(data.message, 'success');
            loadQuotations(); // Refresh quotations list
        } else {
            showNotification(data.error || 'Failed to delete quotation', 'error');
        }
    } catch (error) {
        console.error('Deletion error:', error);
        showNotification('An error occurred while deleting the quotation', 'error');
    }
}

/**
 * Download RFS file
 */
function downloadRFS() {
    console.log('downloadRFS function called');
    console.log('Current URL:', window.location.pathname);
    
    // Get project ID from current page URL
    const projectId = window.location.pathname.match(/\/projects\/(\d+)\//)?.[1];
    console.log('Extracted project ID:', projectId);
    
    if (projectId) {
        const rfsDownloadUrl = `/projects/${projectId}/rfs/download/`;
        console.log('Downloading RFS from:', rfsDownloadUrl);
        window.open(rfsDownloadUrl, '_blank');
    } else {
        console.error('Could not determine project ID for RFS download');
    }
}

// Auto-download RFS if available in session
function checkForAutoDownload() {
    // Check if there's RFS download info in the page
    const rfsInfo = document.querySelector('[data-rfs-download]');
    if (rfsInfo) {
        const downloadPath = rfsInfo.getAttribute('data-rfs-download');
        const filename = rfsInfo.getAttribute('data-rfs-filename');
        
        if (downloadPath) {
            // Trigger download
            const downloadUrl = `/projects/rfs/download/${downloadPath}/`;
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = filename || 'RFS.xlsx';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }
}

/**
 * Get CSRF token from cookies
 */
function getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
}

/**
 * Show notification to user
 */
function showNotification(message, type = 'info') {
    // Create toast container if it doesn't exist
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'fixed top-4 right-4 z-50 space-y-2';
        document.body.appendChild(container);
    }

    // Create toast element
    const toast = document.createElement('div');
    const bgColor = type === 'success' ? 'bg-green-500' : 
                   type === 'error' ? 'bg-red-500' : 
                   type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500';
    
    const icon = type === 'success' ? 
        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />' :
        type === 'error' ?
        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />' :
        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />';

    toast.className = `${bgColor} text-white px-6 py-4 rounded-lg shadow-lg flex items-center gap-3 min-w-80 transform transition-all duration-300 translate-x-full opacity-0`;
    toast.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            ${icon}
        </svg>
        <span class="flex-1">${message}</span>
        <button onclick="this.parentElement.remove()" class="text-white hover:text-gray-200 transition">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
        </button>
    `;

    container.appendChild(toast);

    // Animate in
    setTimeout(() => {
        toast.classList.remove('translate-x-full', 'opacity-0');
    }, 10);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.classList.add('translate-x-full', 'opacity-0');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// Make functions globally available
window.openUploadModal = openUploadModal;
window.closeUploadModal = closeUploadModal;
window.approveQuotation = approveQuotation;
window.deleteQuotation = deleteQuotation;
window.downloadRFS = downloadRFS;
