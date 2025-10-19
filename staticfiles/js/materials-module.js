/**
 * Materials Module for PowerMason
 * Handles materials management functionality with AJAX navigation support
 */

console.log('📦 Materials Module loading...');

// Global variables
let currentEditId = null;
let deleteItemId = null;
let deleteItemName = '';

// Initialize materials module
function initializeMaterials() {
    console.log('📦 Initializing Materials module...');
    
    // Load initial data
    loadMaterials();
    loadStats();
    loadCategories();
    
    // Setup event listeners
    setupMaterialsEventListeners();
    
    console.log('✅ Materials module initialized');
}

// Setup event listeners for materials
function setupMaterialsEventListeners() {
    console.log('🔧 Setting up Materials event listeners...');
    
    // Search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                loadMaterials();
            }
        });
    }
    
    // Filter functionality
    const categoryFilter = document.getElementById('categoryFilter');
    if (categoryFilter) {
        categoryFilter.addEventListener('change', loadMaterials);
    }
    
    // Apply filters button
    const applyFiltersBtn = document.querySelector('button[onclick="loadMaterials()"]');
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', loadMaterials);
    }
}

// Load materials data
async function loadMaterials() {
    console.log('📦 Loading materials...');
    
    // Check if we're in test mode (no materials container)
    const container = document.getElementById('materialsContainer');
    if (!container) {
        console.log('📦 No materials container found - skipping API call');
        return;
    }
    
    try {
        const searchTerm = document.getElementById('searchInput')?.value || '';
        const category = document.getElementById('categoryFilter')?.value || '';
        
        const params = new URLSearchParams();
        if (searchTerm) params.append('search', searchTerm);
        if (category) params.append('category', category);
        
        const response = await fetch(`/materials/materials/?${params.toString()}`);
        const data = await response.json();
        
        if (data.success) {
            displayMaterials(data.materials);
        } else {
            showToast('Error loading materials', 'error');
        }
    } catch (error) {
        console.error('Error loading materials:', error);
        showToast('Error loading materials', 'error');
    }
}

// Display materials in table
function displayMaterials(materials) {
    const container = document.getElementById('materialsContainer');
    if (!container) return;
    
    if (materials.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center py-8">No materials found</p>';
        return;
    }
    
    const tableHTML = `
        <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Unit</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    ${materials.map(material => `
                        <tr class="hover:bg-gray-50">
                            <td class="px-6 py-4 whitespace-nowrap">
                                <div class="text-sm font-medium text-gray-900">${material.name}</div>
                                ${material.description ? `<div class="text-sm text-gray-500">${material.description}</div>` : ''}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${material.category || 'N/A'}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${material.unit}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">₱${parseFloat(material.standard_price).toFixed(2)}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                                <button onclick="editMaterial(${material.id}, '${material.name}', '${material.unit}', ${material.standard_price}, '${material.category || ''}', '${material.description || ''}')" 
                                        class="text-blue-600 hover:text-blue-900">Edit</button>
                                <button onclick="deleteMaterial(${material.id}, '${material.name}')" 
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
        console.log('📦 No stats container found - skipping API call');
        return;
    }
    
    try {
        const response = await fetch('/materials/materials/stats/');
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
                    <p class="text-sm font-medium text-gray-600">Total Materials</p>
                    <p class="text-2xl font-bold text-gray-900">${stats.total_materials || 0}</p>
                </div>
                <div class="w-12 h-12 bg-blue-100 rounded-2xl flex items-center justify-center">
                    <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
                    </svg>
                </div>
            </div>
        </div>
        <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm font-medium text-gray-600">Categories</p>
                    <p class="text-2xl font-bold text-gray-900">${stats.total_categories || 0}</p>
                </div>
                <div class="w-12 h-12 bg-green-100 rounded-2xl flex items-center justify-center">
                    <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"/>
                    </svg>
                </div>
            </div>
        </div>
        <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm font-medium text-gray-600">Avg. Price</p>
                    <p class="text-2xl font-bold text-gray-900">₱${stats.average_price || '0.00'}</p>
                </div>
                <div class="w-12 h-12 bg-yellow-100 rounded-2xl flex items-center justify-center">
                    <svg class="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"/>
                    </svg>
                </div>
            </div>
        </div>
        <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm font-medium text-gray-600">Last Updated</p>
                    <p class="text-sm font-bold text-gray-900">${stats.last_updated || 'Never'}</p>
                </div>
                <div class="w-12 h-12 bg-purple-100 rounded-2xl flex items-center justify-center">
                    <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
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
        console.log('📦 No category filter found - skipping API call');
        return;
    }
    
    try {
        const response = await fetch('/materials/materials/categories/');
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
    document.getElementById('modalTitle').textContent = 'Add Material';
    document.getElementById('materialForm').action = '/materials/materials/create/';
    clearForm();
    currentEditId = null;
    document.getElementById('materialModal').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('materialModal').classList.add('hidden');
    currentEditId = null;
    clearForm();
}

function clearForm() {
    document.getElementById('materialId').value = '';
    document.getElementById('materialName').value = '';
    document.getElementById('materialUnit').value = '';
    document.getElementById('materialPrice').value = '';
    document.getElementById('materialCategory').value = '';
    document.getElementById('materialDescription').value = '';
}

function editMaterial(id, name, unit, price, category, description) {
    currentEditId = id;
    document.getElementById('modalTitle').textContent = 'Edit Material';
    document.getElementById('materialForm').action = `/materials/materials/${id}/edit/`;
    document.getElementById('materialId').value = id;
    document.getElementById('materialName').value = name;
    document.getElementById('materialUnit').value = unit;
    document.getElementById('materialPrice').value = price;
    document.getElementById('materialCategory').value = category;
    document.getElementById('materialDescription').value = description;
    document.getElementById('materialModal').classList.remove('hidden');
}

// Save material
async function saveMaterial(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.querySelector('#submitText').textContent;
    submitBtn.querySelector('#submitText').textContent = 'Saving...';
    submitBtn.disabled = true;

    try {
        const url = currentEditId ? `/materials/materials/${currentEditId}/edit/` : '/materials/materials/create/';

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
            loadMaterials();
            loadStats();
            loadCategories();
            showToast(currentEditId ? 'Material updated successfully' : 'Material created successfully', 'success');
        } else {
            showToast('Error saving material', 'error');
        }
    } catch (error) {
        console.error('Error saving material:', error);
        showToast('Error saving material', 'error');
    } finally {
        submitBtn.querySelector('#submitText').textContent = originalText;
        submitBtn.disabled = false;
    }
}

// Delete functions
function deleteMaterial(id, name) {
    deleteItemId = id;
    deleteItemName = name;
    document.getElementById('deleteMaterialName').textContent = name;
    document.getElementById('deleteModal').classList.remove('hidden');
}

function closeDeleteModal() {
    document.getElementById('deleteModal').classList.add('hidden');
    deleteItemId = null;
    deleteItemName = '';
}

async function confirmDelete() {
    if (!deleteItemId) return;

    const deleteBtn = document.getElementById('deleteButtonText');
    deleteBtn.textContent = 'Deleting...';

    try {
        const response = await fetch(`/materials/materials/${deleteItemId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });

        const data = await response.json();

        if (data.success) {
            closeDeleteModal();
            loadMaterials();
            loadStats();
            showToast('Material deleted successfully', 'success');
        } else {
            showToast('Error deleting material', 'error');
        }
    } catch (error) {
        console.error('Error deleting material:', error);
        showToast('Error deleting material', 'error');
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
    if (window.location.pathname.includes('/materials/')) {
        initializeMaterials();
    }
});

document.addEventListener('ajaxContentLoaded', function(e) {
    if (window.location.pathname.includes('/materials/')) {
        console.log('🔄 Materials: AJAX content loaded, reinitializing...');
        initializeMaterials();
    }
});

// Expose functions globally for onclick handlers
window.initializeMaterials = initializeMaterials;
window.openCreateModal = openCreateModal;
window.closeModal = closeModal;
window.editMaterial = editMaterial;
window.deleteMaterial = deleteMaterial;
window.closeDeleteModal = closeDeleteModal;
window.confirmDelete = confirmDelete;
window.saveMaterial = saveMaterial;
window.loadMaterials = loadMaterials;

console.log('✅ Materials Module loaded');
