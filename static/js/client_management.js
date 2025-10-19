let editingId = null;
let currentClientId = null;

console.log("✅ Client management script loaded");

// Utility functions
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

function showNotification(message, type) {
    const existingNotifications = document.querySelectorAll('.notification-toast');
    existingNotifications.forEach(notif => notif.remove());
    
    const notification = document.createElement('div');
    notification.className = `notification-toast fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transform transition-all duration-300 ${
        type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
    }`;
    notification.innerHTML = `
        <div class="flex items-center">
            <div class="flex-shrink-0">
                ${type === 'success' ? 
                    '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>' :
                    '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path></svg>'
                }
            </div>
            <div class="ml-3">
                <p class="text-sm font-medium">${message}</p>
            </div>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('translate-x-0');
        notification.classList.remove('translate-x-full');
    }, 100);
    
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 4000);
}

function handleClientTypeChange() {
    console.log('Client type changed:', document.getElementById('clientType').value);
}
function openAddModal() {
    document.getElementById('modalTitle').textContent = 'Add Client';
    document.getElementById('clientForm').action = addClientUrl;
    clearForm();
    editingId = null;
    document.getElementById('clientModal').classList.remove('hidden');
    loadProjectTypes();
}

function closeModal() {
    document.getElementById('clientModal').classList.add('hidden');
    editingId = null;
    clearForm();
}

function clearForm() {
    document.getElementById('companyName').value = '';
    document.getElementById('contactName').value = '';
    document.getElementById('email').value = '';
    document.getElementById('phone').value = '';
    document.getElementById('address').value = '';
    document.getElementById('city').value = '';
    document.getElementById('state').value = '';
    document.getElementById('zipCode').value = '';
    document.getElementById('notes').value = '';
    document.getElementById('isActive').checked = true;
    document.getElementById('clientType').value = '';
    
    const projectTypeCheckboxes = document.querySelectorAll('#projectTypesList input[name="project_types"]');
    projectTypeCheckboxes.forEach(checkbox => checkbox.checked = false);
    
    const xeroSyncCheckbox = document.getElementById('syncToXero');
    if (xeroSyncCheckbox) {
        xeroSyncCheckbox.checked = false;
    }
}

function populateFormWithErrorData(formData) {
    if (!formData) return;

    if (formData.company_name) document.getElementById('companyName').value = formData.company_name;
    if (formData.contact_name) document.getElementById('contactName').value = formData.contact_name;
    if (formData.email) document.getElementById('email').value = formData.email;
    if (formData.phone) document.getElementById('phone').value = formData.phone;
    if (formData.address) document.getElementById('address').value = formData.address;
    if (formData.city) document.getElementById('city').value = formData.city;
    if (formData.state) document.getElementById('state').value = formData.state;
    if (formData.zip_code) document.getElementById('zipCode').value = formData.zip_code;
    if (formData.notes) document.getElementById('notes').value = formData.notes;
    if (formData.client_type) document.getElementById('clientType').value = formData.client_type;

    document.getElementById('isActive').checked = formData.is_active !== false;

    const xeroSyncCheckbox = document.getElementById('syncToXero');
    if (xeroSyncCheckbox && formData.sync_to_xero !== undefined) {
        xeroSyncCheckbox.checked = formData.sync_to_xero;
    }

    if (formData.project_types && formData.project_types.length > 0) {
        formData.project_types.forEach(typeId => {
            const checkbox = document.querySelector(`#projectTypesList input[value="${typeId}"]`);
            if (checkbox) checkbox.checked = true;
        });
    }
}
function openEditClientModal(clientId) {
    console.log('Opening edit modal for client ID:', clientId);
    document.getElementById('editClientModal').classList.remove('hidden');
    document.getElementById('editClientForm').action = `/manage-client/clients/edit/${clientId}/`;
    
    window.currentEditClientId = clientId;
    loadEditProjectTypes();
    
    setTimeout(() => {
        loadEditClientData(clientId);
    }, 300);
}

function closeEditModal() {
    document.getElementById('editClientModal').classList.add('hidden');
    document.getElementById('editClientForm').reset();
    
    const clientTypeIndicator = document.getElementById('currentClientTypeIndicator');
    const projectTypesIndicator = document.getElementById('currentProjectTypesIndicator');
    if (clientTypeIndicator) clientTypeIndicator.classList.add('hidden');
    if (projectTypesIndicator) projectTypesIndicator.classList.add('hidden');
    
    const dropdown = document.getElementById('editProjectTypesDropdownMenu');
    if (dropdown) dropdown.classList.add('hidden');
    
    window.editClientProjectTypes = [];
    window.currentEditClientData = {};
}

// Add this to your loadEditClientData function, after the Xero status update
function loadEditClientData(clientId) {
    console.log('Loading client data for edit, ID:', clientId);
    
    fetch(`/manage-client/clients/edit/${clientId}/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',  // This is crucial!
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        console.log('Response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Loaded client data for edit:', data);
        
        if (!data.success) {
            throw new Error('Server returned unsuccessful response');
        }
        
        // The data is nested under data.client in your view response
        const client = data.client;
        window.currentEditClientData = client;
        
        // Populate form fields - use client.property instead of data.property
        document.getElementById('editCompanyName').value = client.company_name || '';
        document.getElementById('editContactName').value = client.contact_name || '';
        document.getElementById('editEmail').value = client.email || '';
        document.getElementById('editPhone').value = client.phone || '';
        document.getElementById('editAddress').value = client.address || '';
        document.getElementById('editCity').value = client.city || '';
        document.getElementById('editState').value = client.state || '';
        document.getElementById('editZipCode').value = client.zip_code || '';
        document.getElementById('editNotes').value = client.notes || '';
        document.getElementById('editIsActive').checked = client.is_active;
        
        // Set client type
        const clientTypeSelect = document.getElementById('editClientType');
        if (clientTypeSelect && client.client_type) {
            clientTypeSelect.value = client.client_type;
            const clientTypeMap = {'DC': 'Direct Client', 'GC': 'General Contractor'};
            const clientTypeName = clientTypeMap[client.client_type] || client.client_type;
            
            const indicator = document.getElementById('currentClientTypeIndicator');
            const indicatorText = document.getElementById('currentClientTypeText');
            if (indicator && indicatorText) {
                indicatorText.textContent = clientTypeName;
                indicator.classList.remove('hidden');
            }
        }
        
        // Handle contract display
        console.log('Contract URL:', client.contract_url);
        console.log('Contract Name:', client.contract_name);
        
        if (client.contract_url && client.contract_name) {
            showEditCurrentContract(client.contract_url, client.contract_name);
        } else {
            showEditCurrentContract(null, null);
        }
        
        // Update Xero status
        updateEditXeroStatus(client);
        
        // Store and handle project types
        window.editClientProjectTypes = client.project_type_ids || [];
        
        if (window.editClientProjectTypes.length > 0) {
            const projectIndicator = document.getElementById('currentProjectTypesIndicator');
            const projectIndicatorText = document.getElementById('currentProjectTypesText');
            if (projectIndicator && projectIndicatorText) {
                projectIndicatorText.textContent = `${window.editClientProjectTypes.length} project type(s)`;
                projectIndicator.classList.remove('hidden');
            }
        }
        
        selectEditStoredProjectTypes();
        
        console.log('✅ Edit modal fully loaded with client data');
    })
    .catch(error => {
        console.error('Error loading client data for edit:', error);
        console.error('Full error details:', error.stack);
        alert('Error loading client data: ' + error.message);
    });
}

// Also add the missing showEditCurrentContract function if it doesn't exist
function showEditCurrentContract(contractUrl, contractName) {
    const currentContractInfo = document.getElementById('editCurrentContractInfo');
    const noContractInfo = document.getElementById('editNoContractInfo');
    const currentContractLink = document.getElementById('editCurrentContractLink');
    const currentContractNameSpan = document.getElementById('editCurrentContractName');
    
    console.log('showEditCurrentContract called with:', contractUrl, contractName);
    
    if (contractUrl && contractName) {
        console.log('✅ Showing contract info');
        if (currentContractLink) currentContractLink.href = contractUrl;
        if (currentContractNameSpan) currentContractNameSpan.textContent = contractName;
        if (currentContractInfo) currentContractInfo.classList.remove('hidden');
        if (noContractInfo) noContractInfo.classList.add('hidden');
    } else {
        console.log('❌ No contract, showing empty state');
        if (currentContractInfo) currentContractInfo.classList.add('hidden');
        if (noContractInfo) noContractInfo.classList.remove('hidden');
    }
}
function toggleEditProjectTypesDropdown() {
    const dropdown = document.getElementById('editProjectTypesDropdownMenu');
    if (dropdown) {
        dropdown.classList.toggle('hidden');
    }
}

function updateEditSelectedProjectTypes() {
    const checkboxes = document.querySelectorAll('#editProjectTypesList input[name="project_types"]:checked');
    const selectedText = document.getElementById('editSelectedProjectTypesText');
    const selectedDisplay = document.getElementById('editSelectedProjectTypesDisplay');
    const selectedTags = document.getElementById('editSelectedProjectTypesTags');
    
    if (!selectedText) return;
    
    if (checkboxes.length === 0) {
        selectedText.textContent = 'Select project types...';
        selectedText.className = 'text-gray-500';
        if (selectedDisplay) selectedDisplay.classList.add('hidden');
    } else {
        selectedText.textContent = `${checkboxes.length} project type(s) selected`;
        selectedText.className = 'text-gray-900';
        if (selectedDisplay) selectedDisplay.classList.remove('hidden');
        
        if (selectedTags) {
            selectedTags.innerHTML = Array.from(checkboxes).map(checkbox => {
                const nameSpan = checkbox.parentElement.querySelector('span .font-medium');
                const name = nameSpan ? nameSpan.textContent.trim() : checkbox.value;
                return `
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        ${name}
                        <button type="button" onclick="removeEditProjectType('${checkbox.id}')" class="ml-1 text-blue-600 hover:text-blue-800">
                            <svg class="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                            </svg>
                        </button>
                    </span>
                `;
            }).join('');
        }
    }
}

function removeEditProjectType(checkboxId) {
    const checkbox = document.getElementById(checkboxId);
    if (checkbox) {
        checkbox.checked = false;
        updateEditSelectedProjectTypes();
    }
}

function loadEditProjectTypes() {
    console.log('Loading project types for edit modal');
    const projectTypesList = document.getElementById('editProjectTypesList');
    const noProjectTypes = document.getElementById('editNoProjectTypes');
    
    if (!projectTypesList) return;
    
    projectTypesList.innerHTML = '<div class="text-sm text-gray-500 p-2">Loading project types...</div>';
    if (noProjectTypes) noProjectTypes.classList.add('hidden');
    
    fetch('/manage-client/api/project-types/active/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Loaded project types for edit:', data);
            
            if (data.project_types && data.project_types.length > 0) {
                if (noProjectTypes) noProjectTypes.classList.add('hidden');
                projectTypesList.innerHTML = data.project_types.map(type => `
                    <label class="flex items-center p-2 hover:bg-gray-100 rounded cursor-pointer">
                        <input type="checkbox" id="edit_type_${type.id}" name="project_types" value="${type.id}"
                               onchange="updateEditSelectedProjectTypes()"
                               class="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500">
                        <span class="ml-2 text-sm text-gray-700">
                            <span class="font-medium">${type.name}</span>
                            ${type.code ? `<span class="text-gray-500 text-xs ml-1">(${type.code})</span>` : ''}
                            ${type.description ? `<div class="text-xs text-gray-600 mt-1">${type.description}</div>` : ''}
                        </span>
                    </label>
                `).join('');
                
                updateEditSelectedProjectTypes();
                selectEditStoredProjectTypes();
            } else {
                projectTypesList.innerHTML = '';
                if (noProjectTypes) noProjectTypes.classList.remove('hidden');
            }
        })
        .catch(error => {
            console.error('Error loading project types for edit:', error);
            projectTypesList.innerHTML = '<div class="text-sm text-red-500 p-2">Error loading project types.</div>';
        });
}

function selectEditStoredProjectTypes() {
    if (window.editClientProjectTypes && window.editClientProjectTypes.length > 0) {
        console.log('Selecting stored project types for edit:', window.editClientProjectTypes);
        
        window.editClientProjectTypes.forEach(typeId => {
            const checkbox = document.getElementById(`edit_type_${typeId}`);
            if (checkbox) {
                checkbox.checked = true;
                console.log(`✓ Checked edit project type ${typeId}`);
            }
        });
        
        updateEditSelectedProjectTypes();
    }
}
function openProjectTypeModal() {
    document.getElementById('projectTypeModal').classList.remove('hidden');
}

function closeProjectTypeModal() {
    document.getElementById('projectTypeModal').classList.add('hidden');
    document.getElementById('projectTypeForm').reset();
    document.getElementById('projectTypeIsActive').checked = true;
}

function loadProjectTypes() {
    const projectTypesList = document.getElementById('projectTypesList');
    const noProjectTypes = document.getElementById('noProjectTypes');
    
    if (!projectTypesList) return;
    
    projectTypesList.innerHTML = '<div class="text-sm text-gray-500">Loading project types...</div>';
    noProjectTypes.classList.add('hidden');
    
    fetch('/manage-client/api/project-types/active/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.project_types && data.project_types.length > 0) {
                noProjectTypes.classList.add('hidden');
                projectTypesList.innerHTML = data.project_types.map(type => `
                    <div class="flex items-center">
                        <input type="checkbox" id="type_${type.id}" name="project_types" value="${type.id}"
                               class="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500">
                        <label for="type_${type.id}" class="ml-2 text-sm text-gray-700">
                            <span class="font-medium">${type.name}</span>
                            ${type.code ? `<span class="text-gray-500 text-xs">(${type.code})</span>` : ''}
                            ${type.description ? `<div class="text-xs text-gray-600">${type.description}</div>` : ''}
                        </label>
                    </div>
                `).join('');
            } else {
                projectTypesList.innerHTML = '';
                noProjectTypes.classList.remove('hidden');
            }
        })
        .catch(error => {
            console.error('Error loading project types:', error);
            projectTypesList.innerHTML = '<div class="text-sm text-red-500">Error loading project types.</div>';
        });
}

// ===== CLIENT DETAILS MODAL FUNCTIONS =====
function openClientDetailsModal(clientId) {
    currentClientId = clientId;
    document.getElementById('clientDetailsModal').classList.remove('hidden');
    loadClientDetails(clientId);
}

function closeClientDetailsModal() {
    document.getElementById('clientDetailsModal').classList.add('hidden');
    currentClientId = null;
}

function loadClientDetails(clientId) {
    fetch(`/manage-client/api/clients/${clientId}/`)
        .then(response => response.json())
        .then(data => {
            // Store client data globally for use in project redirects
            window.currentClientData = data;
            
            // Update header
            document.getElementById('detailsClientName').textContent = data.company_name;
            document.getElementById('detailsContactName').textContent = data.contact_name;

            // Update client info
            const clientInfo = document.getElementById('detailsClientInfo');
            const clientTypeMap = {'DC': 'Direct Client', 'GC': 'General Contractor'};
            
            clientInfo.innerHTML = `
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <span class="text-sm font-medium text-gray-500">Type:</span>
                        <span class="block text-gray-900">${clientTypeMap[data.client_type] || data.client_type}</span>
                    </div>
                    <div>
                        <span class="text-sm font-medium text-gray-500">Status:</span>
                        <span class="block">
                            <span class="px-2 py-1 rounded-full text-xs font-medium ${data.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}">
                                ${data.is_active ? 'Active' : 'Inactive'}
                            </span>
                        </span>
                    </div>
                    ${data.email ? `
                    <div>
                        <span class="text-sm font-medium text-gray-500">Email:</span>
                        <span class="block text-gray-900">${data.email}</span>
                    </div>
                    ` : ''}
                    ${data.phone ? `
                    <div>
                        <span class="text-sm font-medium text-gray-500">Phone:</span>
                        <span class="block text-gray-900">${data.phone}</span>
                    </div>
                    ` : ''}
                    ${data.address ? `
                    <div class="col-span-2">
                        <span class="text-sm font-medium text-gray-500">Address:</span>
                        <span class="block text-gray-900">${data.address}${data.city ? ', ' + data.city : ''}${data.state ? ', ' + data.state : ''} ${data.zip_code || ''}</span>
                    </div>
                    ` : ''}
                    ${data.notes ? `
                    <div class="col-span-2">
                        <span class="text-sm font-medium text-gray-500">Notes:</span>
                        <span class="block text-gray-900">${data.notes}</span>
                    </div>
                    ` : ''}
                </div>
            `;

            // Load project types
            loadClientProjectTypesForDetails(clientId);
            
            // Load projects (placeholder for now)
            loadClientProjects(clientId);
        })
        .catch(error => {
            console.error('Error loading client details:', error);
        });
}

function loadClientProjectTypesForDetails(clientId) {
    fetch(`/manage-client/api/clients/${clientId}/`)
        .then(response => response.json())
        .then(data => {
            const projectTypesContainer = document.getElementById('detailsProjectTypes');
            
            if (data.project_types && data.project_types.length > 0) {
                // Fetch project type names
                fetch('/manage-client/api/project-types/active/')
                    .then(response => response.json())
                    .then(typesData => {
                        const typeNames = typesData.project_types.reduce((acc, type) => {
                            acc[type.id] = type;
                            return acc;
                        }, {});
                        
                        projectTypesContainer.innerHTML = data.project_types.map(typeId => {
                            const type = typeNames[typeId];
                            return type ? `
                                <span class="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                                    ${type.name} ${type.code ? `(${type.code})` : ''}
                                </span>
                            ` : '';
                        }).join('');
                    });
            } else {
                projectTypesContainer.innerHTML = '<span class="text-gray-500 text-sm">No project types assigned</span>';
            }
        });
}

function loadClientProjects(clientId) {
    console.log('loadClientProjects called with clientId:', clientId);
    const projectsList = document.getElementById('detailsProjectsList');
    console.log('projectsList element:', projectsList);
    
    if (!projectsList) {
        console.error('detailsProjectsList element not found!');
        return;
    }
    
    // Show loading state
    projectsList.innerHTML = '<div class="text-gray-500 text-sm">Loading projects...</div>';
    
    // Helper function to truncate text
    function truncateText(text, maxLength = 80) {
        if (!text) return '';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }
    
    fetch(`/manage-client/api/clients/${clientId}/projects/`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Projects data received:', data);
            
            if (data.projects && data.projects.length > 0) {
                projectsList.innerHTML = data.projects.map(project => `
                    <div class="bg-white border border-gray-200 rounded-lg p-3 hover:shadow-md transition-all cursor-pointer hover:border-blue-300 hover:bg-blue-50"
                         onclick="redirectToProjectView(${project.id})">
                        <div class="flex justify-between items-start">
                            <div class="flex-1">
                                <h4 class="font-medium text-blue-600 hover:text-blue-800">${project.project_name}</h4>
                                <p class="text-sm text-gray-600">${project.project_id}</p>
                                ${project.description ? `<p class="text-sm text-gray-500 mt-1" title="${project.description}">${truncateText(project.description)}</p>` : ''}
                            </div>
                            <span class="px-2 py-1 text-xs rounded-full ${getStatusBadgeClass(project.status)}">
                                ${getStatusLabel(project.status)}
                            </span>
                        </div>
                        <div class="mt-2 grid grid-cols-2 gap-2 text-xs text-gray-500">
                            ${project.location ? `<div><strong>Location:</strong> ${project.location}</div>` : ''}
                            ${project.start_date ? `<div><strong>Start:</strong> ${formatDate(project.start_date)}</div>` : ''}
                            ${project.estimated_cost ? `<div><strong>Estimate Cost:</strong> ${formatCurrency(project.estimated_cost)}</div>` : ''}
                            ${project.target_completion_date ? `<div><strong>Target:</strong> ${formatDate(project.target_completion_date)}</div>` : ''}
                        </div>
                        <div class="mt-2 text-xs text-gray-400">Click to view project details</div>
                    </div>
                `).join('');
            } else {
                projectsList.innerHTML = `
                    <div class="text-center text-gray-500 py-6">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2-2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                        </svg>
                        <p class="text-sm">No projects found</p>
                        <p class="text-xs text-gray-400 mt-1">This client has no projects yet</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error fetching client projects:', error);
            projectsList.innerHTML = `
                <div class="text-red-500 text-sm text-center py-4">
                    <p>Error loading projects</p>
                    <button onclick="loadClientProjects(${clientId})" class="text-blue-600 hover:text-blue-800 underline mt-1">
                        Try again
                    </button>
                </div>
            `;
        });
}
// New function to handle project redirection
function redirectToProjectView(projectId) {
    // Using the window variables that are already set in your template
    const token = window.userToken;
    const role = window.userRole;
    
    if (!role || role === 'None' || role === 'null') {
        console.error('Invalid role detected:', role);
        alert('Unable to redirect: Invalid user role. Please refresh the page and try again.');
        return;
    }

    // Get the client type from the stored client data
    if (!window.currentClientData || !window.currentClientData.client_type) {
        console.error('Client data not available for project redirect');
        alert('Client data not available. Please refresh and try again.');
        return;
    }

    const projectSource = window.currentClientData.client_type; // 'DC' or 'GC'
    
    // Build the URL according to your Django pattern: view/<str:project_source>/<int:pk>/
    const url = `/projects/view/${projectSource}/${projectId}/`;
    
    console.log('Redirecting to project view:', url);
    window.location.href = url;
}

// Helper functions for formatting
function getStatusBadgeClass(status) {
    const statusClasses = {
        'PL': 'bg-gray-100 text-gray-800',     // Planned
        'OG': 'bg-blue-100 text-blue-800', // Ongoing
        'CP': 'bg-green-100 text-green-800',   // Completed
        'CN': 'bg-red-100 text-red-800'      // Cancelled
    };
    return statusClasses[status] || 'bg-gray-100 text-gray-800';
}

function getStatusLabel(status) {
    const statusLabels = {
        'PL': 'Planned',
        'OG': 'Ongoing',
        'CP': 'Completed',
        'CN': 'Cancelled'
    };
    return statusLabels[status] || status;
}



function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

function formatCurrency(amount) {
    if (!amount) return 'N/A';
    return new Intl.NumberFormat('en-PH', {
        style: 'currency',
        currency: 'PHP'
    }).format(amount);
}

function createProjectForClient() {
    const clientId = currentClientId;
    const clientName = document.getElementById('detailsClientName').textContent;
        window.location.href = `/manage-client/create-project-for-client/${clientId}/`;
    
}

function confirmDelete(clientId, companyName, projectCount) {
    let message = `Are you sure you want to delete "${companyName}"?`;

    if (projectCount > 0) {
        message = `"${companyName}" is currently used in ${projectCount} project(s). Deleting it will deactivate the client instead of removing it completely.`;
    }

    document.getElementById('deleteMessage').textContent = message;
    document.getElementById('deleteForm').action = `/manage-client/clients/delete/${clientId}/`;
    document.getElementById('deleteModal').classList.remove('hidden');
}

function closeDeleteModal() {
    document.getElementById('deleteModal').classList.add('hidden');
}
function updateEditXeroStatus(clientData) {
    console.log('🚀 updateEditXeroStatus called with:', clientData);
    
    const statusDisplay = document.getElementById('editXeroStatusDisplay');
    const syncCheckbox = document.getElementById('editSyncToXero');
    const manualSyncBtn = document.getElementById('editManualSyncBtn');
    const syncDescription = document.getElementById('editSyncDescription');
    
    if (!statusDisplay) {
        console.log('❌ editXeroStatusDisplay not found - Xero not enabled');
        return;
    }
    
    if (clientData.xero_contact_id) {
        console.log('✅ Client is synced to Xero');
        
        if (syncCheckbox) syncCheckbox.checked = true;
        if (manualSyncBtn) manualSyncBtn.classList.remove('hidden');
        if (syncDescription) syncDescription.textContent = 'Updates will be synced to the existing Xero contact';
        
        statusDisplay.innerHTML = `
            <div class="bg-green-50 border border-green-200 p-3 rounded-lg">
                <div class="flex items-start justify-between">
                    <div class="flex items-center">
                        <svg class="h-5 w-5 text-green-600 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                        </svg>
                        <div>
                            <p class="text-sm font-medium text-green-800">Currently synced to Xero</p>
                            <p class="text-xs text-green-600 mt-1">
                                Contact ID: ${clientData.xero_contact_id.substring(0, 20)}...
                                ${clientData.xero_last_sync ? '<br>Last synced: ' + new Date(clientData.xero_last_sync).toLocaleString() : ''}
                            </p>
                        </div>
                    </div>
                    <a href="https://go.xero.com/Contacts/View/${clientData.xero_contact_id}" target="_blank" 
                       class="text-green-600 hover:text-green-800 p-1 rounded hover:bg-green-100 transition"
                       title="View in Xero">
                        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                        </svg>
                    </a>
                </div>
            </div>
        `;
    } else {
        console.log('⚠️ Client is NOT synced to Xero');
        
        if (syncCheckbox) syncCheckbox.checked = false;
        if (manualSyncBtn) manualSyncBtn.classList.add('hidden');
        if (syncDescription) syncDescription.textContent = 'Will create a new contact in your connected Xero organization';
        
        statusDisplay.innerHTML = `
            <div class="bg-yellow-50 border border-yellow-200 p-3 rounded-lg">
                <div class="flex items-center">
                    <svg class="h-5 w-5 text-yellow-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                    </svg>
                    <div>
                        <p class="text-sm font-medium text-yellow-800">Not synced to Xero</p>
                        <p class="text-xs text-yellow-600 mt-1">This client hasn't been synced to your Xero organization yet.</p>
                    </div>
                </div>
            </div>
        `;
    }
}

function manualSyncClient() {
    const clientId = window.currentEditClientData?.id || 
                     window.currentEditClientId || 
                     document.getElementById('editClientForm').action.match(/\/edit\/(\d+)\//)?.[1];
    
    if (!clientId) {
        alert('Client data not loaded. Please refresh and try again.');
        return;
    }
    
    const syncBtn = document.getElementById('editManualSyncBtn');
    const originalText = syncBtn.textContent;
    
    syncBtn.textContent = 'Syncing...';
    syncBtn.disabled = true;
    syncBtn.innerHTML = '<svg class="h-3 w-3 animate-spin inline mr-1" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>Syncing...';
    
    fetch(`/clients/${clientId}/sync-to-xero/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json',
        },
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Server returned HTML instead of JSON. Check your URL pattern.');
        }
        
        return response.json();
    })
    .then(data => {
        if (data.success) {
            window.currentEditClientData.xero_contact_id = data.xero_contact_id;
            window.currentEditClientData.xero_last_sync = data.last_synced;
            
            updateEditXeroStatus(window.currentEditClientData);
            showNotification('Client successfully synced to Xero!', 'success');
            
        } else {
            throw new Error(data.error || 'Sync failed');
        }
    })
    .catch(error => {
        console.error('Manual sync error:', error);
        alert('Sync failed: ' + error.message);
    })
    .finally(() => {
        syncBtn.textContent = originalText;
        syncBtn.disabled = false;
        syncBtn.innerHTML = originalText;
    });
}

// Function to update client card in the UI
function updateClientCard(clientData) {
    const clientList = document.getElementById('clientCardsContainer');
    if (!clientList) return;

    // Find the existing card by data-client-id
    const existingCard = clientList.querySelector(`.client-card[data-client-id='${clientData.id}']`);

    if (existingCard) {
        existingCard.innerHTML = `
            <!-- Header -->
            <div class="p-6 pb-4">
                <div class="flex justify-between items-start mb-3">
                    <div class="flex-1">
                        <h3 class="text-lg font-semibold text-gray-900 mb-1">${clientData.company_name}</h3>
                        <p class="text-sm text-gray-600 font-medium">${clientData.contact_name || ''}</p>
                    </div>
                    <div class="flex flex-col items-end space-y-1">
                        <span class="px-3 py-1 rounded-full text-xs font-medium ${clientData.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}">
                            ${clientData.is_active ? 'Active' : 'Inactive'}
                        </span>
                        <span class="px-2 py-1 rounded text-xs font-medium ${clientData.client_type === 'DC' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'}">
                            ${clientData.client_type_display || ''}
                        </span>
                    </div>
                </div>

                <!-- Contact Info -->
                <div class="space-y-2 mb-4 text-sm text-gray-600">
                    ${clientData.email ? `
                    <div class="flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                        <span class="truncate">${clientData.email}</span>
                    </div>` : ''}

                    ${clientData.phone ? `
                    <div class="flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                        </svg>
                        <span>${clientData.phone}</span>
                    </div>` : ''}

                    ${clientData.city || clientData.state ? `
                    <div class="flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        <span class="truncate">${clientData.city || ''}${clientData.city && clientData.state ? ', ' : ''}${clientData.state || ''}</span>
                    </div>` : ''}
                </div>

                <!-- Project Types -->
                ${clientData.project_types && clientData.project_types.length ? `
                <div class="mb-4">
                    <div class="text-xs font-medium text-gray-500 mb-2">Project Types:</div>
                    <div class="flex flex-wrap gap-1">
                        ${clientData.project_types.slice(0, 3).map(pt => `
                        <span class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                            ${pt}
                        </span>
                        `).join('')}
                        ${clientData.project_types.length > 3 ? `
                        <span class="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                            +${clientData.project_types.length - 3} more
                        </span>` : ''}
                    </div>
                </div>` : ''}
            </div>

            <!-- Footer -->
            <div class="px-6 py-4 border-t border-gray-200 bg-gray-50">
                <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-500">
                        ${clientData.project_count || 0} project${clientData.project_count === 1 ? '' : 's'}
                    </span>
                    <div class="flex space-x-2">
                        <!-- Edit -->
                        <button 
                            class="edit-btn text-blue-600 hover:text-blue-800 text-sm font-medium transition px-2 py-1 rounded hover:bg-blue-50"
                            data-id="${clientData.id}">
                            Edit
                        </button>

                        <!-- Delete -->
                        ${clientData.can_delete ? `
                        <button 
                            class="delete-btn text-red-600 hover:text-red-800 text-sm font-medium transition px-2 py-1 rounded hover:bg-red-50"
                            data-id="${clientData.id}"
                            data-name="${clientData.company_name}"
                            data-count="${clientData.project_count || 0}">
                            Delete
                        </button>` : ''}
                    </div>
                </div>
            </div>
        `;
        console.log(`✅ Client card updated for: ${clientData.company_name}`);
    } else {
        console.warn('⚠️ Could not find client card to update, adding new one.');
        addClientCardToList(clientData);
    }
}
function addClientCardToList(clientData) {
    const clientList = document.getElementById('clientCardsContainer');
    if (!clientList) return;

    const card = document.createElement('div');
    card.className = 'bg-white rounded-lg border border-gray-200 hover:shadow-lg transition-all duration-200 transform hover:-translate-y-1 cursor-pointer client-card';
    card.setAttribute('data-client-id', clientData.id);

    card.innerHTML = `
        <!-- Header -->
        <div class="p-6 pb-4">
            <div class="flex justify-between items-start mb-3">
                <div class="flex-1">
                    <h3 class="text-lg font-semibold text-gray-900 mb-1">${clientData.company_name}</h3>
                    <p class="text-sm text-gray-600 font-medium">${clientData.contact_name || ''}</p>
                </div>
                <div class="flex flex-col items-end space-y-1">
                    <span class="px-3 py-1 rounded-full text-xs font-medium ${clientData.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}">
                        ${clientData.is_active ? 'Active' : 'Inactive'}
                    </span>
                    <span class="px-2 py-1 rounded text-xs font-medium ${clientData.client_type === 'DC' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'}">
                        ${clientData.client_type_display || ''}
                    </span>
                </div>
            </div>

            <!-- Contact Info -->
            <div class="space-y-2 mb-4 text-sm text-gray-600">
                ${clientData.email ? `
                <div class="flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    <span class="truncate">${clientData.email}</span>
                </div>` : ''}

                ${clientData.phone ? `
                <div class="flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                    </svg>
                    <span>${clientData.phone}</span>
                </div>` : ''}

                ${clientData.city || clientData.state ? `
                <div class="flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <span class="truncate">${clientData.city || ''}${clientData.city && clientData.state ? ', ' : ''}${clientData.state || ''}</span>
                </div>` : ''}
            </div>

            <!-- Project Types -->
            ${clientData.project_types && clientData.project_types.length ? `
            <div class="mb-4">
                <div class="text-xs font-medium text-gray-500 mb-2">Project Types:</div>
                <div class="flex flex-wrap gap-1">
                    ${clientData.project_types.slice(0, 3).map(pt => `
                    <span class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                        ${pt}
                    </span>
                    `).join('')}
                    ${clientData.project_types.length > 3 ? `
                    <span class="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                        +${clientData.project_types.length - 3} more
                    </span>` : ''}
                </div>
            </div>` : ''}
        </div>

        <!-- Footer -->
        <div class="px-6 py-4 border-t border-gray-200 bg-gray-50">
            <div class="flex justify-between items-center">
                <span class="text-sm text-gray-500">
                    ${clientData.project_count || 0} project${clientData.project_count === 1 ? '' : 's'}
                </span>
                <div class="flex space-x-2">
                    <button 
                        class="edit-btn text-blue-600 hover:text-blue-800 text-sm font-medium transition px-2 py-1 rounded hover:bg-blue-50"
                        data-id="${clientData.id}">
                        Edit
                    </button>
                    ${clientData.can_delete ? `
                    <button 
                        class="delete-btn text-red-600 hover:text-red-800 text-sm font-medium transition px-2 py-1 rounded hover:bg-red-50"
                        data-id="${clientData.id}"
                        data-name="${clientData.company_name}"
                        data-count="${clientData.project_count || 0}">
                        Delete
                    </button>` : ''}
                </div>
            </div>
        </div>
    `;

    clientList.prepend(card);
}

// Form submission handler for add client
function handleAddFormSubmission() {
    const addForm = document.getElementById('clientForm');
    if (!addForm) return;

    addForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const formData = new FormData(addForm);

        try {
            const response = await fetch(addForm.action, {
                method: "POST",
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            });

            const data = await response.json();

            if (data.success) {
                console.log("✅ Client added successfully:", data.client);
                showNotification(data.message, "success");
                closeModal();
                // Refresh page or update UI as needed
                setTimeout(() => location.reload(), 1500);
            } else {
                console.warn("❌ Validation errors:", data.errors);
                if (data.errors) data.errors.forEach(err => showNotification(err, "error"));
                if (data.form_data) populateFormWithErrorData(data.form_data);
            }

        } catch (err) {
            console.error("🔥 Error submitting Add Client form:", err);
            showNotification("Network or server error. Please try again.", "error");
        }
    });
}

// Project type form submission
function handleProjectTypeFormSubmission() {
    const projectTypeForm = document.getElementById('projectTypeForm');
    if (!projectTypeForm) return;
    
    projectTypeForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const name = document.getElementById('projectTypeName').value.trim();
        const code = document.getElementById('projectTypeCode').value.trim();
        const description = document.getElementById('projectTypeDescription').value.trim();
        const isActive = document.getElementById('projectTypeIsActive').checked;
        
        if (!name || !code) {
            alert('Project type name and code are required.');
            return;
        }
        
        const submitBtn = document.getElementById('projectTypeSubmitBtn');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creating...';
        
        const requestData = {
            name: name,
            code: code,
            description: description,
            is_active: isActive
        };
        
        fetch('/manage-client/create-project-type/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                closeProjectTypeModal();
                showNotification('Project type "' + data.project_type.name + '" created successfully!', 'success');
                
                // Reload project types for both modals
                loadProjectTypes();
                loadEditProjectTypes();
                
                // Auto-select in add modal
                setTimeout(() => {
                    const newTypeCheckbox = document.getElementById('type_' + data.project_type.id);
                    if (newTypeCheckbox) {
                        newTypeCheckbox.checked = true;
                    }
                }, 1000);
                
            } else {
                alert('Error creating project type: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error creating project type. Please try again.');
        })
        .finally(() => {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        });
    });
}

// Edit form submission handler
function handleEditFormSubmission() {
    const editForm = document.getElementById('editClientForm');
    if (!editForm) return;
    
    editForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const submitButton = this.querySelector('button[type="submit"]');
        const originalButtonText = submitButton.textContent;
        
        submitButton.textContent = 'Updating...';
        submitButton.disabled = true;
        
        fetch(this.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.text();
        })
        .then(text => {
            if (text.trim().startsWith('<!DOCTYPE') || text.trim().startsWith('<html')) {
                throw new Error('Received HTML instead of JSON');
            }
            
            try {
                return JSON.parse(text);
            } catch (e) {
                throw new Error('Invalid JSON response');
            }
        })
        .then(data => {
            if (data.success) {
                showNotification(data.message, 'success');
                closeEditModal();
                updateClientCard(data.client);
                setTimeout(() => location.reload(), 1500);
            } else {
                if (data.errors && data.errors.length > 0) {
                    data.errors.forEach(error => {
                        showNotification(error, 'error');
                    });
                } else {
                    showNotification('An error occurred while updating the client.', 'error');
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('An error occurred. Please try again.', 'error');
        })
        .finally(() => {
            submitButton.textContent = originalButtonText;
            submitButton.disabled = false;
        });
    });
}

// Main event listeners
document.addEventListener('DOMContentLoaded', function() {
     // Initialize form handlers
    handleAddFormSubmission();
    handleEditFormSubmission();
    handleProjectTypeFormSubmission();
    // Add Client buttons
    const addButtons = document.querySelectorAll('#addClientBtn, #addClientBtn2');
    addButtons.forEach(button => {
        if (button) {
            button.addEventListener('click', () => openAddModal());
        }
    });

    // Edit buttons - use event delegation to handle both card and details modal edit buttons
    document.addEventListener('click', function(e) {
        const editBtn = e.target.closest('.edit-btn');

        if (editBtn) {
            e.stopPropagation();
            const clientId = editBtn.getAttribute('data-id');
            console.log('Edit button clicked, clientId:', clientId);
            if (clientId) {
                openEditClientModal(clientId);
            } else {
                console.error('No client ID found on edit button');
            }
        }
    });

    // Delete buttons
    document.addEventListener('click', function(e) {
        const deleteBtn = e.target.closest('.delete-btn');
        if(deleteBtn){
            e.stopPropagation();
            const clientId = deleteBtn.dataset.id;
            const clientName = deleteBtn.dataset.name;
            const projectCount = deleteBtn.dataset.count;
            confirmDelete(clientId, clientName, projectCount);
        }
    });

    // Client details modal close buttons
    const closeDetailsBtn = document.getElementById('closeDetailsBtn');
    const closeDetailsFooterBtn = document.getElementById('closeDetailsFooterBtn');
    if (closeDetailsBtn) {
        closeDetailsBtn.addEventListener('click', closeClientDetailsModal);
    }
    if (closeDetailsFooterBtn) {
        closeDetailsFooterBtn.addEventListener('click', closeClientDetailsModal);
    }

    // Add Project button
    const addProjectBtn = document.getElementById('addProjectBtn');
    if (addProjectBtn) {
        addProjectBtn.addEventListener('click', createProjectForClient);
    }

    // Client card clicks for details modal
document.addEventListener('click', function(e) {
    // Don't open details if clicked on any button or action element
    if (e.target.closest('button') || e.target.closest('.edit-btn') || e.target.closest('.delete-btn')) {
        return;
    }
    
    const clientCard = e.target.closest('.client-card');
    if (clientCard) {
        const clientId = clientCard.getAttribute('data-client-id');
        if (clientId) {
            openClientDetailsModal(parseInt(clientId));
        }
    }
});

    // Search functionality
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        searchInput.addEventListener('keyup', function(e) {
            if (e.target.value === '' && e.key === 'Backspace') {
                window.location.href = clientManagementUrl;
            }
        });
    }
});

// ===== MODAL CLICK OUTSIDE TO CLOSE =====
window.onclick = function(event) {
    const modal = document.getElementById('clientModal');
    const deleteModal = document.getElementById('deleteModal');
    const editModal = document.getElementById('editClientModal');
    const detailsModal = document.getElementById('clientDetailsModal');

    if (event.target === modal) {
        closeModal();
    }
    if (event.target === deleteModal) {
        closeDeleteModal();
    }
    if (event.target === editModal) {
        closeEditModal();
    }
    if (event.target === detailsModal) {
        closeClientDetailsModal();
    }
};
