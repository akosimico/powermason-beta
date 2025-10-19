/**
 * Module Initializer for PowerMason
 * Central registry for all module initialization functions
 * Handles both first load and AJAX navigation
 */

console.log('🔧 Module Initializer loading...');

// Module Registry - Maps URL patterns to initialization functions
window.ModuleRegistry = {
    '/dashboard/': function() { 
        if (typeof window.initializeDashboard === 'function') {
            window.initializeDashboard();
        }
    },
    '/manage-client/': function() { 
        if (typeof window.initializeClientManagement === 'function') {
            window.initializeClientManagement();
        }
    },
    '/materials/': function() { 
        if (typeof window.initializeMaterials === 'function') {
            window.initializeMaterials();
        }
    },
    '/equipment/': function() { 
        if (typeof window.initializeEquipment === 'function') {
            window.initializeEquipment();
        }
    },
    '/price-monitoring/': function() { 
        if (typeof window.initializePriceMonitoring === 'function') {
            window.initializePriceMonitoring();
        }
    },
    '/projects/': function() { 
        if (typeof window.initializeProjects === 'function') {
            window.initializeProjects();
        }
    },
    '/employees/': function() { 
        if (typeof window.initializeEmployees === 'function') {
            window.initializeEmployees();
        }
    },
    '/scheduling/': function() { 
        if (typeof window.initializeScheduling === 'function') {
            window.initializeScheduling();
        }
    },
    '/progress/': function() { 
        if (typeof window.initializeProgress === 'function') {
            window.initializeProgress();
        }
    },
    '/budgets/': function() { 
        if (typeof window.initializeBudgets === 'function') {
            window.initializeBudgets();
        }
    }
};

// Global function registry for onclick handlers
window.GlobalFunctions = {};

// Register common global functions
function registerGlobalFunctions() {
    // Upload modal functions
    window.openUploadModal = function() {
        console.log('📁 Upload modal requested');
        const uploadModal = document.getElementById('uploadModal') || document.getElementById('fileUploadModal');
        if (uploadModal) {
            uploadModal.classList.remove('hidden');
            console.log('📁 Upload modal opened');
        } else {
            console.warn('📁 Upload modal not found in DOM');
            alert('Upload functionality is not available in this view');
        }
    };

    window.closeUploadModal = function() {
        console.log('📁 Closing upload modal');
        const uploadModal = document.getElementById('uploadModal') || document.getElementById('fileUploadModal');
        if (uploadModal) {
            uploadModal.classList.add('hidden');
        }
    };

    // Register in global functions
    window.GlobalFunctions['openUploadModal'] = window.openUploadModal;
    window.GlobalFunctions['closeUploadModal'] = window.closeUploadModal;
}

/**
 * Initialize the current module based on URL
 */
function initializeCurrentModule() {
    console.log('🏗️ Module Initializer: Initializing current module...');
    
    const path = window.location.pathname;
    console.log('📍 Current path:', path);
    
    // Find matching module pattern
    let matchedModule = null;
    for (let pattern in ModuleRegistry) {
        if (path.includes(pattern)) {
            matchedModule = pattern;
            break;
        }
    }
    
    if (matchedModule) {
        const initFunction = ModuleRegistry[matchedModule];
        console.log(`🎯 Found module: ${matchedModule}`);
        
        // Call the initialization function
        if (typeof initFunction === 'function') {
            try {
                console.log(`🚀 Calling module initializer for ${matchedModule}...`);
                initFunction();
                console.log(`✅ Module ${matchedModule} initialized successfully`);
            } catch (error) {
                console.error(`❌ Error initializing module ${matchedModule}:`, error);
            }
        } else {
            console.warn(`⚠️ No initializer function found for ${matchedModule}`);
        }
    } else {
        console.log('ℹ️ No specific module pattern matched, using fallback initialization');
        // Fallback: try to initialize any available modules
        initializeFallbackModules();
    }
}

/**
 * Fallback initialization for modules without specific patterns
 */
function initializeFallbackModules() {
    console.log('🔄 Module Initializer: Running fallback initialization...');
    
    // Try common initialization functions
    const commonInitFunctions = [
        'initializeDashboard',
        'initializeClientManagement',
        'initializeMaterials',
        'initializeEquipment',
        'initializeProjects',
        'initializeEmployees'
    ];
    
    commonInitFunctions.forEach(funcName => {
        if (typeof window[funcName] === 'function') {
            try {
                console.log(`🔄 Trying fallback: ${funcName}`);
                window[funcName]();
            } catch (error) {
                console.warn(`⚠️ Fallback ${funcName} failed:`, error);
            }
        }
    });
}

/**
 * Register a global function for onclick handlers
 */
function registerGlobalFunction(name, func) {
    window.GlobalFunctions[name] = func;
    window[name] = func; // Also attach to window for direct access
    console.log(`📝 Registered global function: ${name}`);
}

/**
 * Setup event delegation for common patterns
 */
function setupGlobalEventDelegation() {
    console.log('🔧 Module Initializer: Setting up global event delegation...');
    
    // Modal handling
    document.addEventListener('click', function(e) {
        // Modal open triggers
        if (e.target.matches('[data-modal-trigger]')) {
            e.preventDefault();
            const modalId = e.target.dataset.modalId;
            if (modalId) {
                const modal = document.getElementById(modalId);
                if (modal) {
                    modal.classList.remove('hidden');
                    console.log('📱 Modal opened:', modalId);
                }
            }
        }
        
        // Modal close triggers
        if (e.target.matches('[data-modal-close]')) {
            e.preventDefault();
            const modalId = e.target.dataset.modalId;
            if (modalId) {
                const modal = document.getElementById(modalId);
                if (modal) {
                    modal.classList.add('hidden');
                    console.log('📱 Modal closed:', modalId);
                }
            }
        }
        
        // Generic button actions
        if (e.target.matches('[data-action]')) {
            const action = e.target.dataset.action;
            const handler = window.GlobalFunctions[action];
            if (handler && typeof handler === 'function') {
                e.preventDefault();
                handler(e);
            }
        }
    });
    
    // Form handling
    document.addEventListener('submit', function(e) {
        const form = e.target;
        if (form.hasAttribute('data-ajax-form')) {
            e.preventDefault();
            const handler = window.GlobalFunctions['submitAjaxForm'];
            if (handler && typeof handler === 'function') {
                handler(form);
            }
        }
    });
    
    console.log('✅ Global event delegation setup complete');
}

/**
 * Initialize all modules and setup
 */
function initializeAllModules() {
    console.log('🚀 Module Initializer: Starting initialization...');
    
    // Register global functions first
    registerGlobalFunctions();
    
    // Setup global event delegation
    setupGlobalEventDelegation();
    
    // Initialize current module
    initializeCurrentModule();
    
    console.log('✅ Module Initializer: Initialization complete');
}

// Listen for both DOM ready and AJAX content loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM Content Loaded - Module Initializer');
    initializeAllModules();
});

document.addEventListener('ajaxContentLoaded', function(e) {
    console.log('🔄 AJAX Content Loaded - Module Initializer');
    console.log('📍 AJAX URL:', e.detail?.url);
    initializeAllModules();
});

// Expose functions globally
window.initializeCurrentModule = initializeCurrentModule;
window.initializeAllModules = initializeAllModules;
window.registerGlobalFunction = registerGlobalFunction;

console.log('✅ Module Initializer loaded and ready');
