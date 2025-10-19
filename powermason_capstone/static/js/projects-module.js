/**
 * Projects Module for PowerMason
 * Handles projects management functionality with AJAX navigation support
 */

console.log('📋 Projects Module loading...');

// Initialize projects module
function initializeProjects() {
    console.log('📋 Initializing Projects module...');
    
    // Setup event listeners
    setupProjectsEventListeners();
    
    console.log('✅ Projects module initialized');
}

// Setup event listeners for projects
function setupProjectsEventListeners() {
    console.log('🔧 Setting up Projects event listeners...');
    
    // Add any project-specific event listeners here
    // This is a placeholder for future project functionality
}

// Global functions for onclick handlers
window.openProjectModal = function() {
    console.log('📋 Project modal requested');
    const projectModal = document.getElementById('projectModal') || document.getElementById('addProjectModal');
    if (projectModal) {
        projectModal.classList.remove('hidden');
        console.log('📋 Project modal opened');
    } else {
        console.warn('📋 Project modal not found in DOM');
        alert('Project functionality is not available in this view');
    }
};

window.closeProjectModal = function() {
    console.log('📋 Closing project modal');
    const projectModal = document.getElementById('projectModal') || document.getElementById('addProjectModal');
    if (projectModal) {
        projectModal.classList.add('hidden');
    }
};

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname.includes('/projects/')) {
        initializeProjects();
    }
});

document.addEventListener('ajaxContentLoaded', function(e) {
    if (window.location.pathname.includes('/projects/')) {
        console.log('🔄 Projects: AJAX content loaded, reinitializing...');
        initializeProjects();
    }
});

// Expose functions globally for onclick handlers
window.initializeProjects = initializeProjects;

console.log('✅ Projects Module loaded');



