/**
 * Equipment Module for PowerMason
 * Handles equipment management functionality with AJAX navigation support
 */

console.log('🔧 Equipment Module loading...');

// Global variables
let equipmentEditId = null;
let equipmentDeleteItemId = null;
let equipmentDeleteItemName = '';

// Initialize equipment module
function initializeEquipment() {
    console.log('🔧 Initializing Equipment module...');
    
    // Load initial data
    loadEquipment();
    loadStats();
    loadCategories();
    
    // Setup event listeners
    setupEquipmentEventListeners();
    
    console.log('✅ Equipment module initialized');
}

// Setup event listeners for equipment
function setupEquipmentEventListeners() {
    console.log('🔧 Setting up Equipment event listeners...');
    
    // Search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                loadEquipment();
            }
        });
    }
    
    // Filter functionality
    const categoryFilter = document.getElementById('categoryFilter');
    if (categoryFilter) {
        categoryFilter.addEventListener('change', loadEquipment);
    }
    
    // Apply filters button
    const applyFiltersBtn = document.querySelector('button[onclick="loadEquipment()"]');
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', loadEquipment);
    }
}

// Load equipment data
async function loadEquipment() {
    console.log('🔧 Loading equipment...');
    
    // Check if we're in test mode (no equipment container)
    const container = document.getElementById('equipmentContainer');
    if (!container) {
        console.log('🔧 No equipment container found - skipping API call');
        return;
    }
    
    try {
        const searchTerm = document.getElementById('searchInput')?.value || '';
        const category = document.getElementById('categoryFilter')?.value || '';
        
        const params = new URLSearchParams();
        if (searchTerm) params.append('search', searchTerm);
        if (category) params.append('category', category);
        
        const response = await fetch(`/materials/equipment/?${params.toString()}`);
        const data = await response.json();
        
        if (data.success) {
            displayEquipment(data.equipment);
        } else {
            showToast('Error loading equipment', 'error');
        }
    } catch (error) {
        console.error('Error loading equipment:', error);
        showToast('Error loading equipment', 'error');
    }
}

// Display equipment in table
function displayEquipment(equipment) {
    const container = document.getElementById('equipmentContainer');
    if (!container) return;
    
    if (equipment.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center py-8">No equipment found</p>';
        return;
    }
    
    const tableHTML = `
        <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    ${equipment.map(item => `
                        <tr class="hover:bg-gray-50">
                            <td class="px-6 py-4 whitespace-nowrap">
                                <div class="text-sm font-medium text-gray-900">${item.name}</div>
                                ${item.description ? `<div class="text-sm text-gray-500">${item.description}</div>` : ''}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${item.category || 'N/A'}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${item.equipment_type || 'N/A'}</td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                    item.status === 'available' ? 'bg-green-100 text-green-800' :
                                    item.status === 'in_use' ? 'bg-yellow-100 text-yellow-800' :
                                    'bg-red-100 text-red-800'
                                }">
                                    ${item.status || 'Unknown'}
                                </span>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                                <button onclick="editEquipment(${item.id}, '${item.name}', '${item.equipment_type || ''}', '${item.category || ''}', '${item.description || ''}', '${item.status || ''}')" 
                                        class="text-blue-600 hover:text-blue-900">Edit</button>
                                <button onclick="deleteEquipment(${item.id}, '${item.name}')" 
                                        class="text-red-600 hover:text-red-900">Delete</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = tableHTML;
}

// Load statistics
async function loadStats() {
    // Check if we're in test mode (no stats container)
    const container = document.getElementById('statsContainer');
    if (!container) {
        console.log('🔧 No stats container found - skipping API call');
        return;
    }
    
    try {
        const response = await fetch('/materials/equipment/stats/');
        const data = await response.json();
        
        if (data.success) {
            displayStats(data.stats);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Display statistics
function displayStats(stats) {
    const container = document.getElementById('statsContainer');
    if (!container) return;
    
    container.innerHTML = `
        <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm font-medium text-gray-600">Total Equipment</p>
                    <p class="text-2xl font-bold text-gray-900">${stats.total_equipment || 0}</p>
                </div>
                <div class="w-12 h-12 bg-blue-100 rounded-2xl flex items-center justify-center">
                    <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>
                    </svg>
                </div>
            </div>
        </div>
        <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm font-medium text-gray-600">Available</p>
                    <p class="text-2xl font-bold text-green-600">${stats.available || 0}</p>
                </div>
                <div class="w-12 h-12 bg-green-100 rounded-2xl flex items-center justify-center">
                    <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                </div>
            </div>
        </div>
        <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm font-medium text-gray-600">In Use</p>
                    <p class="text-2xl font-bold text-yellow-600">${stats.in_use || 0}</p>
                </div>
                <div class="w-12 h-12 bg-yellow-100 rounded-2xl flex items-center justify-center">
                    <svg class="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                </div>
            </div>
        </div>
        <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm font-medium text-gray-600">Maintenance</p>
                    <p class="text-2xl font-bold text-red-600">${stats.maintenance || 0}</p>
                </div>
                <div class="w-12 h-12 bg-red-100 rounded-2xl flex items-center justify-center">
                    <svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                    </svg>
                </div>
            </div>
        </div>
    `;
}

// Load categories for filter
async function loadCategories() {
    // Check if we're in test mode (no category filter)
    const select = document.getElementById('categoryFilter');
    if (!select) {
        console.log('🔧 No category filter found - skipping API call');
        return;
    }
    
    try {
        const response = await fetch('/materials/equipment/categories/');
        const data = await response.json();
        
        if (data.success) {
            displayCategories(data.categories);
        }
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

// Display categories in filter dropdown
function displayCategories(categories) {
    const select = document.getElementById('categoryFilter');
    if (!select) return;
    
    const currentValue = select.value;
    select.innerHTML = '<option value="">All Categories</option>' + 
        categories.map(cat => `<option value="${cat}">${cat}</option>`).join('');
    
    if (currentValue) {
        select.value = currentValue;
    }
}

// Modal functions
function openCreateModal() {
    document.getElementById('modalTitle').textContent = 'Add Equipment';
    document.getElementById('equipmentForm').action = '/materials/equipment/create/';
    clearForm();
    currentEditId = null;
    document.getElementById('equipmentModal').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('equipmentModal').classList.add('hidden');
    currentEditId = null;
    clearForm();
}

function clearForm() {
    document.getElementById('equipmentId').value = '';
    document.getElementById('equipmentName').value = '';
    document.getElementById('equipmentType').value = '';
    document.getElementById('equipmentCategory').value = '';
    document.getElementById('equipmentDescription').value = '';
    document.getElementById('equipmentStatus').value = 'available';
}

function editEquipment(id, name, type, category, description, status) {
    equipmentEditId = id;
    document.getElementById('modalTitle').textContent = 'Edit Equipment';
    document.getElementById('equipmentForm').action = `/materials/equipment/${id}/edit/`;
    document.getElementById('equipmentId').value = id;
    document.getElementById('equipmentName').value = name;
    document.getElementById('equipmentType').value = type;
    document.getElementById('equipmentCategory').value = category;
    document.getElementById('equipmentDescription').value = description;
    document.getElementById('equipmentStatus').value = status;
    document.getElementById('equipmentModal').classList.remove('hidden');
}

// Save equipment
async function saveEquipment(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.querySelector('#submitText').textContent;
    submitBtn.querySelector('#submitText').textContent = 'Saving...';
    submitBtn.disabled = true;

    try {
        const url = equipmentEditId ? `/materials/equipment/${equipmentEditId}/edit/` : '/materials/equipment/create/';

        const response = await fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });

        const data = await response.json();

        if (data.success) {
            closeModal();
            loadEquipment();
            loadStats();
            loadCategories();
            showToast(equipmentEditId ? 'Equipment updated successfully' : 'Equipment created successfully', 'success');
        } else {
            showToast('Error saving equipment', 'error');
        }
    } catch (error) {
        console.error('Error saving equipment:', error);
        showToast('Error saving equipment', 'error');
    } finally {
        submitBtn.querySelector('#submitText').textContent = originalText;
        submitBtn.disabled = false;
    }
}

// Delete functions
function deleteEquipment(id, name) {
    equipmentDeleteItemId = id;
    equipmentDeleteItemName = name;
    document.getElementById('deleteEquipmentName').textContent = name;
    document.getElementById('deleteModal').classList.remove('hidden');
}

function closeDeleteModal() {
    document.getElementById('deleteModal').classList.add('hidden');
    equipmentDeleteItemId = null;
    equipmentDeleteItemName = '';
}

async function confirmDelete() {
    if (!equipmentDeleteItemId) return;

    const deleteBtn = document.getElementById('deleteButtonText');
    deleteBtn.textContent = 'Deleting...';

    try {
        const response = await fetch(`/materials/equipment/${equipmentDeleteItemId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });

        const data = await response.json();

        if (data.success) {
            closeDeleteModal();
            loadEquipment();
            loadStats();
            showToast('Equipment deleted successfully', 'success');
        } else {
            showToast('Error deleting equipment', 'error');
        }
    } catch (error) {
        console.error('Error deleting equipment:', error);
        showToast('Error deleting equipment', 'error');
    } finally {
        deleteBtn.textContent = 'Delete';
    }
}

// Utility functions
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
}

function showToast(message, type) {
    const toast = document.createElement('div');
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        info: 'bg-blue-500'
    };

    toast.className = `fixed top-4 right-4 ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg z-50 transition-all duration-300 transform translate-x-full`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.remove('translate-x-full');
    }, 100);

    setTimeout(() => {
        toast.classList.add('translate-x-full');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname.includes('/equipment/')) {
        initializeEquipment();
    }
});

document.addEventListener('ajaxContentLoaded', function(e) {
    if (window.location.pathname.includes('/equipment/')) {
        console.log('🔄 Equipment: AJAX content loaded, reinitializing...');
        initializeEquipment();
    }
});

// Expose functions globally for onclick handlers
window.initializeEquipment = initializeEquipment;
window.openCreateModal = openCreateModal;
window.closeModal = closeModal;
window.editEquipment = editEquipment;
window.deleteEquipment = deleteEquipment;
window.closeDeleteModal = closeDeleteModal;
window.confirmDelete = confirmDelete;
window.saveEquipment = saveEquipment;
window.loadEquipment = loadEquipment;

console.log('✅ Equipment Module loaded');
