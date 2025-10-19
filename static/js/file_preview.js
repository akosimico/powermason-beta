/**
 * File Preview and Data Extraction System
 * Handles file upload, preview, and data extraction for project creation
 */

class FilePreviewManager {
    constructor() {
        this.previewModal = null;
        this.currentFile = null;
        this.extractedData = null;
        this.projectId = null;
        this.init();
    }

    init() {
        this.createPreviewModal();
        this.bindEvents();
    }

    createPreviewModal() {
        const modalHTML = `
            <div id="filePreviewModal" class="fixed inset-0 bg-black bg-opacity-50 items-center justify-center z-50 hidden">
                <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
                    <!-- Modal Header -->
                    <div class="p-6 border-b border-gray-200">
                        <div class="flex justify-between items-center">
                            <h2 class="text-2xl font-bold text-gray-900">File Preview & Data Extraction</h2>
                            <button onclick="filePreviewManager.closeModal()" class="text-gray-400 hover:text-gray-600">
                                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                </svg>
                            </button>
                        </div>
                    </div>

                    <!-- Modal Content -->
                    <div class="p-6">
                        <!-- File Info -->
                        <div id="fileInfo" class="mb-6 hidden">
                            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                <h3 class="text-lg font-semibold text-blue-900 mb-2">File Information</h3>
                                <div id="fileInfoContent" class="text-sm text-blue-800"></div>
                            </div>
                        </div>

                        <!-- Loading State -->
                        <div id="loadingState" class="text-center py-8">
                            <div class="inline-flex items-center">
                                <svg class="animate-spin h-8 w-8 text-blue-600 mr-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                <span class="text-gray-700 font-medium">Processing file...</span>
                            </div>
                        </div>

                        <!-- Error State -->
                        <div id="errorState" class="hidden">
                            <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                                <div class="flex">
                                    <svg class="h-5 w-5 text-red-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
                                    </svg>
                                    <div class="ml-3">
                                        <h3 class="text-sm font-medium text-red-800">Error Processing File</h3>
                                        <div id="errorMessage" class="mt-1 text-sm text-red-700"></div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Preview Content -->
                        <div id="previewContent" class="hidden">
                            <!-- Summary -->
                            <div class="mb-6">
                                <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                                    <h3 class="text-lg font-semibold text-green-900 mb-2">Extraction Summary</h3>
                                    <div id="extractionSummary" class="text-sm text-green-800"></div>
                                </div>
                            </div>

                            <!-- Data Tabs -->
                            <div class="mb-6">
                                <div class="border-b border-gray-200">
                                    <nav class="-mb-px flex space-x-8">
                                        <button class="preview-tab active border-b-2 border-blue-500 py-2 px-1 text-sm font-medium text-blue-600" data-tab="tasks">
                                            Tasks
                                        </button>
                                        <button class="preview-tab border-b-2 border-transparent py-2 px-1 text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300" data-tab="costs">
                                            Costs
                                        </button>
                                        <button class="preview-tab border-b-2 border-transparent py-2 px-1 text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300" data-tab="materials">
                                            Materials
                                        </button>
                                        <button class="preview-tab border-b-2 border-transparent py-2 px-1 text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300" data-tab="equipment">
                                            Equipment
                                        </button>
                                    </nav>
                                </div>

                                <!-- Tab Content -->
                                <div class="mt-4">
                                    <!-- Tasks Tab -->
                                    <div id="tasksTab" class="preview-tab-content">
                                        <div id="tasksContent" class="space-y-3"></div>
                                    </div>

                                    <!-- Costs Tab -->
                                    <div id="costsTab" class="preview-tab-content hidden">
                                        <div id="costsContent" class="space-y-3"></div>
                                    </div>

                                    <!-- Materials Tab -->
                                    <div id="materialsTab" class="preview-tab-content hidden">
                                        <div id="materialsContent" class="space-y-3"></div>
                                    </div>

                                    <!-- Equipment Tab -->
                                    <div id="equipmentTab" class="preview-tab-content hidden">
                                        <div id="equipmentContent" class="space-y-3"></div>
                                    </div>
                                </div>
                            </div>

                            <!-- Suggestions -->
                            <div class="mb-6">
                                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                                    <h3 class="text-lg font-semibold text-yellow-900 mb-2">Suggestions</h3>
                                    <ul id="suggestionsList" class="text-sm text-yellow-800 space-y-1"></ul>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Modal Footer -->
                    <div class="px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-lg">
                        <div class="flex items-center justify-between">
                            <div class="text-sm text-gray-600">
                                <span id="fileStatus">Ready to process</span>
                            </div>
                            <div class="flex space-x-3">
                                <button onclick="filePreviewManager.closeModal()" class="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50">
                                    Cancel
                                </button>
                                <button id="saveDataBtn" onclick="filePreviewManager.saveExtractedData()" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed" disabled>
                                    Apply Data to Project
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.previewModal = document.getElementById('filePreviewModal');
    }

    bindEvents() {
        // Tab switching
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('preview-tab')) {
                this.switchTab(e.target.dataset.tab);
            }
        });
    }

    async processFile(file, projectId = null) {
        this.currentFile = file;
        this.projectId = projectId;
        
        this.showModal();
        this.showLoading();
        this.hideError();
        this.hidePreview();

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/projects/api/file-preview/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.extractedData = result.data;
                this.displayPreview();
            } else {
                this.showError(result.error || 'Failed to process file');
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        }
    }

    displayPreview() {
        this.hideLoading();
        this.showPreview();
        this.updateFileInfo();
        this.updateSummary();
        this.updateTabs();
        this.updateSuggestions();
        // Don't auto-enable save button - let user decide
        // this.enableSaveButton();
    }

    updateFileInfo() {
        const fileInfo = this.extractedData.file_info;
        const fileInfoContent = document.getElementById('fileInfoContent');
        
        fileInfoContent.innerHTML = `
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <span class="font-medium">File Name:</span> ${fileInfo.name}
                </div>
                <div>
                    <span class="font-medium">File Type:</span> ${fileInfo.type.toUpperCase()}
                </div>
                <div>
                    <span class="font-medium">File Size:</span> ${this.formatFileSize(fileInfo.size)}
                </div>
                <div>
                    <span class="font-medium">Status:</span> <span class="text-green-600">Processed Successfully</span>
                </div>
            </div>
        `;
        
        document.getElementById('fileInfo').classList.remove('hidden');
    }

    updateSummary() {
        const summary = this.extractedData.preview.summary;
        document.getElementById('extractionSummary').textContent = summary;
    }

    updateTabs() {
        const mappedModels = this.extractedData.mapped_models;
        
        // Update tasks
        this.updateTabContent('tasks', mappedModels.tasks, 'task_name', 'description');
        
        // Update costs
        this.updateTabContent('costs', mappedModels.budgets, 'description', 'amount');
        
        // Update materials
        this.updateTabContent('materials', mappedModels.materials, 'name', 'quantity');
        
        // Update equipment
        this.updateTabContent('equipment', mappedModels.equipment, 'name', 'notes');
    }

    updateTabContent(tabName, items, primaryField, secondaryField) {
        const content = document.getElementById(`${tabName}Content`);
        
        if (!items || items.length === 0) {
            content.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <svg class="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                    <p>No ${tabName} found in this file</p>
                </div>
            `;
            return;
        }

        content.innerHTML = items.map((item, index) => `
            <div class="bg-white border border-gray-200 rounded-lg p-4">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <h4 class="font-medium text-gray-900">${item[primaryField] || 'Untitled'}</h4>
                        ${item[secondaryField] ? `<p class="text-sm text-gray-600 mt-1">${item[secondaryField]}</p>` : ''}
                        ${item.notes ? `<p class="text-xs text-gray-500 mt-2">${item.notes}</p>` : ''}
                    </div>
                    <div class="ml-4">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            ${tabName.slice(0, -1)}
                        </span>
                    </div>
                </div>
            </div>
        `).join('');
    }

    updateSuggestions() {
        const suggestions = this.extractedData.preview.suggestions;
        const suggestionsList = document.getElementById('suggestionsList');
        
        suggestionsList.innerHTML = suggestions.map(suggestion => `
            <li class="flex items-start">
                <svg class="w-4 h-4 text-yellow-600 mt-0.5 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
                </svg>
                ${suggestion}
            </li>
        `).join('');
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.preview-tab').forEach(tab => {
            tab.classList.remove('active', 'text-blue-600', 'border-blue-500');
            tab.classList.add('text-gray-500', 'border-transparent');
        });
        
        const activeTab = document.querySelector(`[data-tab="${tabName}"]`);
        activeTab.classList.add('active', 'text-blue-600', 'border-blue-500');
        activeTab.classList.remove('text-gray-500', 'border-transparent');
        
        // Update tab content
        document.querySelectorAll('.preview-tab-content').forEach(content => {
            content.classList.add('hidden');
        });
        
        document.getElementById(`${tabName}Tab`).classList.remove('hidden');
    }

    async saveExtractedData() {
        if (!this.projectId) {
            this.showError('Project ID is required to save data');
            return;
        }

        const saveBtn = document.getElementById('saveDataBtn');
        const originalText = saveBtn.textContent;
        saveBtn.disabled = true;
        saveBtn.textContent = 'Saving...';

        try {
            const response = await fetch('/projects/api/save-extracted-data/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({
                    project_id: this.projectId,
                    extracted_data: this.extractedData
                })
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess(result.message);
                setTimeout(() => {
                    this.closeModal();
                }, 2000);
            } else {
                this.showError(result.error || 'Failed to save data');
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        } finally {
            saveBtn.disabled = false;
            saveBtn.textContent = originalText;
        }
    }

    showModal() {
        this.previewModal.classList.remove('hidden');
        this.previewModal.classList.add('flex');
    }

    closeModal() {
        this.previewModal.classList.add('hidden');
        this.previewModal.classList.remove('flex');
        this.resetModal();
    }

    showLoading() {
        document.getElementById('loadingState').classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loadingState').classList.add('hidden');
    }

    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('errorState').classList.remove('hidden');
        document.getElementById('fileStatus').textContent = 'Error processing file';
    }

    hideError() {
        document.getElementById('errorState').classList.add('hidden');
    }

    showPreview() {
        document.getElementById('previewContent').classList.remove('hidden');
        document.getElementById('fileStatus').textContent = 'Data extracted successfully';
    }

    hidePreview() {
        document.getElementById('previewContent').classList.add('hidden');
    }

    enableSaveButton() {
        document.getElementById('saveDataBtn').disabled = false;
    }

    resetModal() {
        this.currentFile = null;
        this.extractedData = null;
        this.hideError();
        this.hidePreview();
        this.hideLoading();
        document.getElementById('fileInfo').classList.add('hidden');
        document.getElementById('saveDataBtn').disabled = true;
        document.getElementById('fileStatus').textContent = 'Ready to process';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    showSuccess(message) {
        // Create a temporary success message
        const successDiv = document.createElement('div');
        successDiv.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
        successDiv.textContent = message;
        document.body.appendChild(successDiv);
        
        setTimeout(() => {
            successDiv.remove();
        }, 3000);
    }
}

// Initialize the file preview manager
const filePreviewManager = new FilePreviewManager();

// Export for global access
window.filePreviewManager = filePreviewManager;
