// Dashboard Initialization Manager
// Ensures proper loading order and prevents conflicts

(function() {
    'use strict';

    // Configuration
    const INIT_CONFIG = {
        enableLeaflet: true,
        enablePerformanceMonitoring: true,
        maxInitRetries: 3,
        initTimeout: 10000
    };

    let initAttempts = 0;
    let isInitialized = false;

    // Initialization queue
    const initQueue = [];

    // Add to initialization queue
    function queueInit(name, fn, dependencies = []) {
        initQueue.push({ name, fn, dependencies, completed: false });
    }

    // Check if dependencies are met
    function dependenciesMet(dependencies) {
        return dependencies.every(dep => window[dep] !== undefined);
    }

    // Execute initialization queue
    function executeInitQueue() {
        if (isInitialized) return;

        const pending = initQueue.filter(item => !item.completed);
        let completedThisRound = 0;

        pending.forEach(item => {
            if (dependenciesMet(item.dependencies)) {
                try {
                    console.log(`🚀 Initializing ${item.name}...`);
                    item.fn();
                    item.completed = true;
                    completedThisRound++;
                    console.log(`✅ ${item.name} initialized successfully`);
                } catch (error) {
                    console.error(`❌ Failed to initialize ${item.name}:`, error);
                }
            }
        });

        // Check if all components are initialized
        const allCompleted = initQueue.every(item => item.completed);

        if (allCompleted) {
            isInitialized = true;
            console.log('🎉 Dashboard initialization completed!');

            // Dispatch custom event
            window.dispatchEvent(new CustomEvent('dashboardInitialized', {
                detail: { initTime: Date.now() }
            }));
        } else if (completedThisRound === 0) {
            initAttempts++;

            if (initAttempts < INIT_CONFIG.maxInitRetries) {
                console.warn(`⚠️ Retrying initialization (attempt ${initAttempts}/${INIT_CONFIG.maxInitRetries})`);
                setTimeout(executeInitQueue, 1000);
            } else {
                console.error('❌ Dashboard initialization failed after maximum retries');
                showInitError();
            }
        } else {
            // Some components initialized, continue
            setTimeout(executeInitQueue, 100);
        }
    }

    // Show initialization error
    function showInitError() {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed top-4 left-4 right-4 bg-red-500 text-white p-4 rounded-lg shadow-lg z-50';
        errorDiv.innerHTML = `
            <div class="flex items-center justify-between">
                <div>
                    <h3 class="font-bold text-lg">Dashboard Initialization Failed</h3>
                    <p class="text-sm">Some components failed to load. Please refresh the page.</p>
                </div>
                <button onclick="window.location.reload()" class="bg-red-700 hover:bg-red-800 px-4 py-2 rounded font-medium transition-colors">
                    Refresh
                </button>
            </div>
        `;
        document.body.appendChild(errorDiv);
    }

    // Register initialization functions
    function registerInits() {
        // Performance monitoring (no dependencies)
        queueInit('Performance Monitor', () => {
            if (INIT_CONFIG.enablePerformanceMonitoring && typeof DashboardPerformanceMonitor !== 'undefined') {
                window.dashboardPerformance = new DashboardPerformanceMonitor();
            }
        });

        // Leaflet map (depends on L)
        queueInit('Leaflet Map', () => {
            if (INIT_CONFIG.enableLeaflet && typeof L !== 'undefined' && typeof initializeMap === 'function') {
                // Clear any existing map
                const mapContainer = document.getElementById('projectsMap');
                if (mapContainer) {
                    mapContainer.innerHTML = '';
                }

                initializeMap();
            }
        }, ['L']);

        // Charts (depends on Chart)
        queueInit('Charts', () => {
            if (typeof Chart !== 'undefined' && window.dashboardData?.projects) {
                const { projects } = window.dashboardData;

                if (typeof initializeProgressChart === 'function') {
                    initializeProgressChart(projects);
                }

                if (typeof initializeBudgetChart === 'function') {
                    initializeBudgetChart(projects);
                }
            }
        }, ['Chart']);

        // Calendar (depends on FullCalendar)
        queueInit('Calendar', () => {
            if (typeof FullCalendar !== 'undefined' && typeof initializeCalendar === 'function') {
                initializeCalendar();
            }
        }, ['FullCalendar']);
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            registerInits();
            executeInitQueue();
        });
    } else {
        registerInits();
        executeInitQueue();
    }

    // Timeout fallback
    setTimeout(() => {
        if (!isInitialized) {
            console.warn('⚠️ Dashboard initialization timeout, forcing completion');
            initAttempts = INIT_CONFIG.maxInitRetries;
            executeInitQueue();
        }
    }, INIT_CONFIG.initTimeout);

    // Export for debugging
    window.DashboardInit = {
        getQueue: () => initQueue,
        isInitialized: () => isInitialized,
        forceInit: executeInitQueue,
        getConfig: () => INIT_CONFIG
    };

})();