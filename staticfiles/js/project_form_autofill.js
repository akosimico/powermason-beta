// Project Form Auto-fill and Project Manager Autocomplete
// File: static/js/project_form_autofill.js

console.log('Project form autofill script loaded');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing...');
    initializeProjectManagerAutocomplete();
    initializeAutoFill();
});

// ===== PROJECT MANAGER AUTOCOMPLETE =====
function initializeProjectManagerAutocomplete() {
    const pmInput = document.getElementById("project_manager_input");
    const pmHidden = document.getElementById("project_manager_id");
    const pmSuggestions = document.getElementById("pm_suggestions");
    
    if (!pmInput || !pmHidden || !pmSuggestions) return;

    let pmTimeout;

    // Fetch project managers
    function searchPMs(query) {
        fetch(`/projects/search/project-managers/?q=${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(data => {
                pmSuggestions.innerHTML = "";
                if (data.length === 0) {
                    pmSuggestions.innerHTML = '<li class="p-2 text-gray-500">No results</li>';
                } else {
                    data.forEach(pm => {
                        const li = document.createElement("li");
                        li.className = "p-2 hover:bg-gray-100 cursor-pointer";
                        li.innerHTML = `<div class="font-medium">${pm.full_name}</div>
                                      <div class="text-sm text-gray-600">${pm.email}</div>`;
                        li.onclick = () => selectPM(pm);
                        pmSuggestions.appendChild(li);
                    });
                }
                pmSuggestions.classList.remove("hidden");
            })
            .catch(err => console.error("Error fetching PMs:", err));
    }

    // Select PM
    function selectPM(pm) {
        pmInput.value = pm.full_name;
        pmHidden.value = pm.id;
        document.getElementById("assigned_pm_display").innerHTML =
            `Assigned to: ${pm.full_name} (${pm.email})`;
        pmSuggestions.classList.add("hidden");
    }

    // Input listener
    pmInput.addEventListener("input", function() {
        clearTimeout(pmTimeout);
        const query = this.value.trim();
        if (query.length < 2) {
            pmSuggestions.classList.add("hidden");
            return;
        }
        pmTimeout = setTimeout(() => searchPMs(query), 300);
    });

    // Hide dropdown when clicking outside
    document.addEventListener("click", (e) => {
        const pmContainer = document.getElementById("pm_container");
        if (pmContainer && !pmContainer.contains(e.target)) {
            pmSuggestions.classList.add("hidden");
        }
    });
}

// ===== AUTO-FILL FUNCTIONALITY =====
function initializeAutoFill() {
    console.log('Initializing auto-fill...');
    
    // Get data from template via JSON script tag
    const dataScript = document.getElementById('django-data');
    let formData = {};
    
    if (dataScript) {
        try {
            formData = JSON.parse(dataScript.textContent);
            console.log('Form data loaded:', formData);
        } catch (e) {
            console.error('Error parsing Django data:', e);
            return;
        }
    } else {
        console.error('django-data script not found');
        return;
    }
    
    if (formData.autoFillMode && formData.preSelectedClientId) {
        console.log('Auto-fill mode active, pre-selected client:', formData.preSelectedClientId);
        markAutoFilledFields();
        showAutoFillNotification(formData.preSelectedClientName);
    }
    
    // Handle client changes for dynamic auto-fill
    const clientField = document.getElementById('id_client');
    if (clientField && !clientField.hasAttribute('readonly')) {
        clientField.addEventListener('change', function() {
            if (this.value) {
                handleClientChange(this.value);
            }
        });
    }
}

function markAutoFilledFields() {
    console.log('Marking auto-filled fields...');
    
    // Only mark payment_terms and project_type as auto-filled (removed location fields)
    const autoFilledFields = ['payment_terms', 'project_type'];
    
    autoFilledFields.forEach(fieldName => {
        const field = document.getElementById(`id_${fieldName}`);
        if (field && field.value) {
            console.log(`Marking field ${fieldName} as auto-filled with value:`, field.value);
            field.classList.add('auto-filled');
            
            // Add label indicator
            const label = document.querySelector(`label[for="id_${fieldName}"]`);
            if (label) {
                label.classList.add('auto-filled-label');
            }
        }
    });
    
    // Show client details if pre-selected
    const formData = getFormData();
    if (formData.preSelectedClientId) {
        console.log('Showing client details for:', formData.preSelectedClientId);
        showClientDetails(formData.preSelectedClientId);
    }
}

function showAutoFillNotification(clientName) {
    if (!clientName) return;
    
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-3 rounded-lg shadow-lg z-50 max-w-sm';
    notification.innerHTML = `
        <div class="flex items-center">
            <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
            </svg>
            <div>
                <p class="font-medium">Auto-filled successfully!</p>
                <p class="text-sm opacity-90">Form populated with ${clientName} data</p>
            </div>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Remove notification after 4 seconds
    setTimeout(() => {
        notification.remove();
    }, 4000);
}

// Handle client change for dynamic auto-fill
function handleClientChange(clientId) {
    if (!clientId) {
        hideClientDetails();
        return;
    }
    
    fetch(`/manage-client/api/clients/${clientId}/`)
        .then(response => response.json())
        .then(data => {
            autoFillFromClientData(data);
            updateProjectTypes(data.project_types);
        })
        .catch(error => {
            console.error('Error fetching client data:', error);
            showErrorNotification('Error loading client data');
        });
}

function autoFillFromClientData(clientData) {
    // Only auto-fill payment terms (removed location auto-fill)
    const paymentTermsField = document.getElementById('id_payment_terms');
    if (paymentTermsField && !paymentTermsField.value) {
        let paymentTerms = '';
        if (clientData.client_type === 'GC') {
            paymentTerms = 'Net 30 days';
        } else if (clientData.client_type === 'DC') {
            paymentTerms = 'Net 15 days';
        }
        
        if (paymentTerms) {
            paymentTermsField.value = paymentTerms;
            paymentTermsField.classList.add('auto-filled');
            
            // Add label indicator
            const paymentTermsLabel = document.querySelector('label[for="id_payment_terms"]');
            if (paymentTermsLabel) {
                paymentTermsLabel.classList.add('auto-filled-label');
            }
        }
    }
    
    // Show client details
    showClientDetails(clientData.id);
}

function updateProjectTypes(clientProjectTypes) {
    const projectTypeField = document.getElementById('id_project_type');
    if (!projectTypeField || !clientProjectTypes) return;
    
    fetch('/manage-client/api/project-types/active/')
        .then(response => response.json())
        .then(data => {
            // Clear existing options except the first empty option
            while (projectTypeField.children.length > 1) {
                projectTypeField.removeChild(projectTypeField.lastChild);
            }
            
            // Add only client's project types
            data.project_types.forEach(type => {
                if (clientProjectTypes.includes(type.id)) {
                    const option = document.createElement('option');
                    option.value = type.id;
                    option.textContent = `${type.name} ${type.code ? '(' + type.code + ')' : ''}`;
                    projectTypeField.appendChild(option);
                }
            });
            
            // Auto-select first available type
            if (projectTypeField.children.length > 1) {
                projectTypeField.selectedIndex = 1;
                projectTypeField.classList.add('auto-filled');
                
                // Add label indicator
                const projectTypeLabel = document.querySelector('label[for="id_project_type"]');
                if (projectTypeLabel) {
                    projectTypeLabel.classList.add('auto-filled-label');
                }
                
                // Trigger change event if there are other dependent fields
                projectTypeField.dispatchEvent(new Event('change'));
            }
        })
        .catch(error => {
            console.error('Error fetching project types:', error);
        });
}

// ===== CLIENT DETAILS FUNCTIONALITY =====
function showClientDetails(clientId) {
    console.log('showClientDetails called with clientId:', clientId);
    
    if (!clientId) {
        console.log('No client ID provided');
        return;
    }
    
    const detailsBox = document.getElementById('client-details-box');
    const detailsContent = document.getElementById('client-details-content');
    
    if (!detailsBox || !detailsContent) {
        console.error('Client details elements not found:', {
            detailsBox: !!detailsBox,
            detailsContent: !!detailsContent
        });
        return;
    }
    
    console.log('Loading client details...');
    
    // Show loading state
    detailsContent.innerHTML = '<div class="text-gray-500">Loading client details...</div>';
    detailsBox.classList.remove('hidden');
    
    fetch(`/manage-client/api/clients/${clientId}/`)
        .then(response => {
            console.log('API response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Client data received:', data);
            
            const clientTypeMap = {
                'DC': 'Direct Client',
                'GC': 'General Contractor'
            };
            
            let detailsHTML = `
                <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
                <div><strong>Company:</strong> ${data.company_name || 'N/A'}</div>
                    <div><strong>Type:</strong> ${clientTypeMap[data.client_type] || data.client_type}</div>
                    <div><strong>Contact Person:</strong> ${data.contact_name || 'N/A'}</div>
            `;
            
            if (data.email) {
                detailsHTML += `<div><strong>Email:</strong> ${data.email}</div>`;
            }
            if (data.phone) {
                detailsHTML += `<div><strong>Phone:</strong> ${data.phone}</div>`;
            }
            if (data.address) {
                detailsHTML += `<div class="md:col-span-2"><strong>Address:</strong> ${data.address}`;
                if (data.city || data.state) {
                    detailsHTML += `, ${data.city || ''} ${data.state || ''}`.replace(/,\s*$/, '');
                }
                if (data.zip_code) {
                    detailsHTML += ` ${data.zip_code}`;
                }
                detailsHTML += `</div>`;
            }
            
            detailsHTML += '</div>';
            
            // Add project types if available
            if (data.project_types && data.project_types.length > 0) {
                fetch('/manage-client/api/project-types/active/')
                    .then(response => response.json())
                    .then(typesData => {
                        const typeNames = typesData.project_types
                            .filter(type => data.project_types.includes(type.id))
                            .map(type => `${type.name} ${type.code ? '(' + type.code + ')' : ''}`)
                            .join(', ');
                        
                        if (typeNames) {
                            detailsHTML += `<div class="mt-2 pt-2 border-t border-gray-200">
                                <strong>Available Project Types:</strong> ${typeNames}
                            </div>`;
                        }
                        
                        detailsContent.innerHTML = detailsHTML;
                    })
                    .catch(() => {
                        detailsContent.innerHTML = detailsHTML;
                    });
            } else {
                detailsContent.innerHTML = detailsHTML;
            }
        })
        .catch(error => {
            console.error('Error fetching client details:', error);
            detailsContent.innerHTML = '<div class="text-red-500">Error loading client details</div>';
        });
}

function hideClientDetails() {
    const detailsBox = document.getElementById('client-details-box');
    if (detailsBox) {
        detailsBox.classList.add('hidden');
    }
}

// ===== UTILITY FUNCTIONS =====
function getFormData() {
    const dataScript = document.getElementById('django-data');
    if (dataScript) {
        try {
            return JSON.parse(dataScript.textContent);
        } catch (e) {
            console.error('Error parsing Django data:', e);
        }
    }
    return {};
}

function removeAutoFillIndicators(fieldName) {
    const field = document.getElementById(`id_${fieldName}`);
    const label = document.querySelector(`label[for="id_${fieldName}"]`);
    
    if (field) {
        field.classList.remove('auto-filled');
    }
    if (label) {
        label.classList.remove('auto-filled-label');
    }
}

function showErrorNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-3 rounded-lg shadow-lg z-50 max-w-sm';
    notification.innerHTML = `
        <div class="flex items-center">
            <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
            </svg>
            <div>
                <p class="font-medium">Error</p>
                <p class="text-sm opacity-90">${message}</p>
            </div>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Remove notification after 5 seconds
    setTimeout(() => {
        notification.remove();
    }, 5000);
}