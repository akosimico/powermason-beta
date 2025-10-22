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
    if (uploadBtn) {
        uploadBtn.addEventListener('click', openUploadModal);
    }
    
    // Upload form submission
    const uploadForm = document.getElementById('quotationUploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleQuotationUpload);
    }
    
    // File input change for auto-calculation
    const fileInput = document.getElementById('quotation_file');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileChange);
    }
}

/**
 * Open upload quotation modal
 */
function openUploadModal() {
    const modal = document.getElementById('uploadQuotationModal');
    if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
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
    }
}

/**
 * Handle file input change for auto-calculation
 */
function handleFileChange(event) {
    const file = event.target.files[0];
    const totalAmountInput = document.getElementById('total_amount');
    
    if (file && file.name.toLowerCase().endsWith('.xlsx') || file.name.toLowerCase().endsWith('.xls')) {
        // Show message that amount will be auto-calculated
        totalAmountInput.placeholder = 'Will be auto-calculated from Excel file';
        totalAmountInput.disabled = true;
    } else {
        totalAmountInput.placeholder = '0.00';
        totalAmountInput.disabled = false;
    }
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
    // This would update the table dynamically if needed
    // For now, the template handles the display
    // In a more advanced implementation, you could update the table without page reload
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
        } else {
            showNotification(data.error || 'Failed to approve quotation', 'error');
        }
    } catch (error) {
        console.error('Approval error:', error);
        showNotification('An error occurred while approving the quotation', 'error');
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
    // Get RFS URL from the page (it should be available in the RFS section)
    const rfsUrl = document.querySelector('a[href*="/media/"]')?.href;
    if (rfsUrl) {
        window.open(rfsUrl, '_blank');
    } else {
        // Fallback to API endpoint
        window.open(`/projects/${currentProjectId}/rfs/download/`, '_blank');
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
