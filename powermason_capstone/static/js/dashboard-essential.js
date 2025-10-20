// dashboard-essential.js - Streamlined Dashboard with Core Project Features
// Focus: Charts, Project Maps, Calendar, and Project Management

// ====================================================================
// UTILITY FUNCTIONS
// ====================================================================

function showLoadingOverlay() {
    const overlay = document.getElementById("loadingOverlay");
    if (overlay) {
        overlay.classList.remove("hidden");
    }
}

function hideLoadingOverlay() {
    const overlay = document.getElementById("loadingOverlay");
    if (overlay) {
        overlay.classList.add("hidden");
    }
}

function showSuccessMessage(message) {
    showToast(message, 'success');
}

function showErrorMessage(message) {
    showToast(message, 'error');
}

function showInfoMessage(message) {
    showToast(message, 'info');
}

function showToast(message, type = 'info', duration = null) {
    const toast = document.createElement('div');
    const colors = {
        success: 'bg-gradient-to-r from-green-500 to-green-600',
        error: 'bg-gradient-to-r from-red-500 to-red-600',
        info: 'bg-gradient-to-r from-blue-500 to-blue-600',
        warning: 'bg-gradient-to-r from-yellow-500 to-yellow-600'
    };

    const icons = {
        success: '✓',
        error: '✕',
        info: 'ℹ',
        warning: '⚠'
    };

    toast.className = `fixed top-4 right-4 ${colors[type]} text-white px-6 py-4 rounded-xl shadow-lg z-50 transition-all duration-500 transform translate-x-full opacity-0 backdrop-blur-sm`;
    toast.innerHTML = `
        <div class="flex items-center space-x-3">
            <span class="text-lg">${icons[type]}</span>
            <span class="font-medium">${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-white hover:text-gray-200 transition-colors">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                </svg>
            </button>
        </div>
    `;

    document.body.appendChild(toast);

    requestAnimationFrame(() => {
        toast.style.transform = 'translateX(0)';
        toast.style.opacity = '1';
    });

    const autoDismissTime = duration || (type === 'error' ? 6000 : type === 'success' ? 2000 : 3000);
    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.transform = 'translateX(100%)';
            toast.style.opacity = '0';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, 500);
        }
    }, autoDismissTime);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function handleResize() {
    if (window.progressChart) {
        window.progressChart.resize();
    }
    if (window.budgetChart) {
        window.budgetChart.resize();
    }
    if (window.dashboardCalendar) {
        window.dashboardCalendar.updateSize();
    }
    if (window.projectMap) {
        window.projectMap.invalidateSize();
    }
}

let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(handleResize, 250);
});

// ====================================================================
// MAIN DASHBOARD INITIALIZATION
// ====================================================================

document.addEventListener("DOMContentLoaded", () => {
    console.log("Essential Dashboard loading...");

    // Load project JSON data
    const dataEl = document.getElementById("projects-data");
    if (!dataEl) {
        console.error("No projects-data element found");
        showErrorMessage("Dashboard data not found. Please refresh the page.");
        return;
    }

    let projects = [];
    try {
        projects = JSON.parse(dataEl.textContent);
        console.log(`Loaded ${projects.length} projects`);
    } catch (err) {
        console.error("Failed to parse projects JSON:", err);
        showErrorMessage("Failed to load dashboard data. Please refresh the page.");
        return;
    }

    // Store projects globally for other modules
    window.dashboardData = { 
        projects,
        timestamp: Date.now()
    };

    // Initialize all components with proper timing
    initializeEssentialDashboard();
});

// Also initialize when window loads (for external libraries)
window.addEventListener('load', () => {
    if (window.dashboardData && !window.dashboardInitialized) {
        console.log("Window loaded, reinitializing dashboard...");
        initializeEssentialDashboard();
    }
});

function initializeEssentialDashboard() {
    // Prevent duplicate initialization
    if (window.dashboardInitialized) {
        console.log("Dashboard already initialized, skipping...");
        return;
    }

    try {
        // Extract and store token and role from URL path
        const pathParts = window.location.pathname.split('/');
        window.dashboardToken = pathParts[2] || "";
        window.dashboardRole = pathParts[3] || "";

        console.log('URL Path:', window.location.pathname);
        console.log('Stored Token:', window.dashboardToken);
        console.log('Stored Role:', window.dashboardRole);

        // Initialize components in order with proper timing
        console.log('🔍 DEBUG: Initializing charts...');
        initializeCharts();
        
        console.log('🔍 DEBUG: Initializing calendar...');
        initializeCalendar();
        
        // Initialize map with delay to ensure Leaflet is loaded
        console.log('🔍 DEBUG: Scheduling map initialization in 500ms...');
        setTimeout(() => {
            console.log('🔍 DEBUG: Executing delayed map initialization...');
            initializeProjectMap();
        }, 500);
        
        console.log('🔍 DEBUG: Initializing interactions...');
        initializeInteractions();

        // Add loading states and animations
        hideLoadingOverlay();

        // Mark as initialized
        window.dashboardInitialized = true;

        console.log("Essential Dashboard initialized successfully");

    } catch (error) {
        console.error("Dashboard initialization failed:", error);
        showErrorMessage("Dashboard initialization failed. Please refresh the page.");
    }
}

// ====================================================================
// CHARTS FUNCTIONALITY
// ====================================================================

function initializeCharts() {
    if (!window.dashboardData?.projects) {
        console.error("No projects data available for charts");
        return;
    }

    const { projects } = window.dashboardData;
    
    initializeProgressChart(projects);
    initializeBudgetChart(projects);
}

// Progress Chart (Horizontal Bar)
function initializeProgressChart(projects) {
    const chartEl = document.getElementById("progressChart");
    if (!chartEl) return;

    const ctx = chartEl.getContext("2d");
    
    const config = {
        type: "bar",
        data: {
            labels: projects.map(p => p.name || p.project_name || 'Unnamed Project'),
            datasets: [
                {
                    label: "Estimate Progress",
                    data: projects.map(p => p.planned_progress || 0),
                    backgroundColor: "rgba(249, 115, 22, 0.8)",
                    borderColor: "rgba(249, 115, 22, 1)",
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false,
                },
                {
                    label: "Actual Progress",
                    data: projects.map(p => p.actual_progress || 0),
                    backgroundColor: "rgba(139, 92, 246, 0.8)",
                    borderColor: "rgba(139, 92, 246, 1)",
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false,
                }
            ]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            layout: { padding: { top: 10, bottom: 10 } },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    cornerRadius: 12,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.x}%`;
                        },
                        afterLabel: function(context) {
                            const chartData = context.chart.data;
                            const planned = chartData.datasets[0].data[context.dataIndex] || 0;
                            const actual = chartData.datasets[1].data[context.dataIndex] || 0;
                            const variance = actual - planned;
                            const status = variance >= 0 ? 'ahead' : 'behind';

                            return variance !== 0
                                ? `${Math.abs(variance)}% ${status} progress`
                                : 'On track';
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: 'rgba(0, 0, 0, 0.05)', drawBorder: false },
                    ticks: {
                        callback: value => value + "%",
                        font: { size: 12, weight: 'bold' },
                        color: '#6b7280'
                    }
                },
                y: {
                    grid: { display: false },
                    ticks: {
                        font: { size: 13, weight: 'bold' },
                        color: '#374151',
                        maxRotation: 0
                    }
                }
            },
            animation: { duration: 2000, easing: 'easeInOutQuart' },
            interaction: { intersect: false, mode: 'index' }
        }
    };

    window.progressChart = new Chart(ctx, config);
    console.log("Progress chart initialized");
}

// Budget Chart (Line Chart)
function initializeBudgetChart(projects) {
    const budgetChartEl = document.getElementById("budgetChart");
    if (!budgetChartEl) return;

    const ctx = budgetChartEl.getContext("2d");

    // Map project budget data with enhanced structure
    const estimatedData = projects.map(p => Number(p.budget_total?.estimated) || 0);
    const approvedData  = projects.map(p => Number(p.budget_total?.approved) || 0);
    const plannedData   = projects.map(p => Number(p.budget_total?.planned) || 0);
    const allocatedData = projects.map(p => Number(p.budget_total?.allocated) || 0);
    const spentData     = projects.map(p => Number(p.budget_total?.spent) || 0);

    const labels = projects.map(p => p.name || p.project_name || 'Unnamed Project');

    const config = {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "Estimated Cost",
                    data: estimatedData,
                    borderColor: "rgba(255, 99, 132, 1)",
                    backgroundColor: "rgba(255, 99, 132, 0.1)",
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: "rgba(255, 99, 132, 1)",
                    pointBorderColor: "#ffffff",
                    pointBorderWidth: 3,
                    pointRadius: 6,
                    pointHoverRadius: 8
                },
                {
                    label: "Approved Budget",
                    data: approvedData,
                    borderColor: "rgba(59, 130, 246, 1)",
                    backgroundColor: "rgba(59, 130, 246, 0.1)",
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: "rgba(59, 130, 246, 1)",
                    pointBorderColor: "#ffffff",
                    pointBorderWidth: 3,
                    pointRadius: 6,
                    pointHoverRadius: 8
                },
                {
                    label: "Planned Budget",
                    data: plannedData,
                    borderColor: "rgba(249, 115, 22, 1)",
                    backgroundColor: "rgba(249, 115, 22, 0.1)",
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: "rgba(249, 115, 22, 1)",
                    pointBorderColor: "#ffffff",
                    pointBorderWidth: 3,
                    pointRadius: 6,
                    pointHoverRadius: 8
                },
                {
                    label: "Allocated Budget",
                    data: allocatedData,
                    borderColor: "rgba(139, 92, 246, 1)",
                    backgroundColor: "rgba(139, 92, 246, 0.1)",
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: "rgba(139, 92, 246, 1)",
                    pointBorderColor: "#ffffff",
                    pointBorderWidth: 3,
                    pointRadius: 6,
                    pointHoverRadius: 8
                },
                {
                    label: "Spent Budget",
                    data: spentData,
                    borderColor: "rgba(34, 197, 94, 1)",
                    backgroundColor: "rgba(34, 197, 94, 0.1)",
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: "rgba(34, 197, 94, 1)",
                    pointBorderColor: "#ffffff",
                    pointBorderWidth: 3,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: { padding: { top: 20, bottom: 10 } },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: 'white',
                    bodyColor: 'white',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    cornerRadius: 12,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ₱${context.parsed.y.toLocaleString()}`;
                        },
                        afterBody: function(tooltipItems) {
                            if (tooltipItems.length > 0) {
                                const dataIndex = tooltipItems[0].dataIndex;
                                const remaining = allocatedData[dataIndex] - spentData[dataIndex];
                                const utilization = allocatedData[dataIndex] > 0
                                    ? ((spentData[dataIndex] / allocatedData[dataIndex]) * 100).toFixed(1)
                                    : 0;

                                return [
                                    `Remaining: ₱${remaining.toLocaleString()}`,
                                    `Utilization: ${utilization}%`
                                ];
                            }
                            return [];
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(0, 0, 0, 0.05)', drawBorder: false },
                    ticks: { font: { size: 12, weight: 'bold' }, color: '#6b7280', maxRotation: 45 }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(0, 0, 0, 0.05)', drawBorder: false },
                    ticks: { callback: value => "₱" + value.toLocaleString(), font: { size: 12, weight: 'bold' }, color: '#6b7280' }
                }
            },
            animation: { duration: 2000, easing: 'easeInOutQuart' },
            interaction: { intersect: false, mode: 'index' }
        }
    };

    if (window.budgetChart && typeof window.budgetChart.update === "function") {
        window.budgetChart.data = config.data;
        window.budgetChart.options = config.options;
        window.budgetChart.update("active");
        console.log("Budget chart updated");
    } else {
        window.budgetChart = new Chart(ctx, config);
        console.log("Budget chart initialized");
    }
}

// ====================================================================
// CALENDAR FUNCTIONALITY
// ====================================================================

function generateProjectColors(projects) {
    const projectColors = {};
    const palette = [
        "#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6",
        "#EC4899", "#14B8A6", "#F97316", "#84CC16", "#06B6D4",
        "#6366F1", "#8B5A2B"
    ];

    let colorIndex = 0;
    projects.forEach(project => {
        const projectName = project.project_name || project.name || "Unknown Project";
        if (!projectColors[projectName]) {
            projectColors[projectName] = palette[colorIndex % palette.length];
            colorIndex++;
        }
    });

    return projectColors;
}

function initializeCalendar() {
    const calendarEl = document.getElementById("taskCalendar");
    if (!calendarEl || !window.dashboardData?.projects) return;

    const { projects } = window.dashboardData;
    const projectColors = generateProjectColors(projects);
    const events = generateCalendarEvents(projects, projectColors);

    window.dashboardCalendar = new FullCalendar.Calendar(calendarEl, {
        initialView: "dayGridMonth",
        height: 'auto',
        contentHeight: 'auto',
        expandRows: true,

        headerToolbar: {
            left: "prev,next today",
            center: "title",
            right: "dayGridMonth,dayGridWeek,dayGridDay,listWeek"
        },

        dayMaxEvents: 3,
        eventDisplay: "block",
        eventTextColor: "#fff",

        events: events,

        // Enhanced Event Styling with Status Indicators
        eventDidMount: info => {
            const event = info.event;
            const props = event.extendedProps;
            
            // Base styling
            info.el.style.borderRadius = "6px";
            info.el.style.padding = "2px 6px";
            info.el.style.fontSize = "0.85rem";
            info.el.style.fontWeight = "500";
            info.el.style.boxShadow = "0 1px 2px rgba(0,0,0,0.1)";
            info.el.style.cursor = "pointer";
            info.el.style.position = "relative";

            // Status indicator
            const statusDot = document.createElement("div");
            statusDot.style.position = "absolute";
            statusDot.style.top = "2px";
            statusDot.style.right = "2px";
            statusDot.style.width = "6px";
            statusDot.style.height = "6px";
            statusDot.style.borderRadius = "50%";
            statusDot.style.border = "1px solid rgba(255,255,255,0.8)";
            
            // Status colors
            const statusColors = {
                'completed': '#10B981',
                'CP': '#10B981',
                'in_progress': '#F59E0B',
                'IP': '#F59E0B',
                'pending': '#6B7280',
                'PL': '#6B7280',
                'overdue': '#EF4444'
            };
            
            if (props.is_overdue) {
                statusDot.style.backgroundColor = statusColors.overdue;
                info.el.style.opacity = "0.8";
                info.el.style.borderLeft = "3px solid #EF4444";
            } else {
                statusDot.style.backgroundColor = statusColors[props.status] || statusColors.pending;
            }
            
            info.el.appendChild(statusDot);

            // Progress bar
            const progress = props.progress || 0;
            if (progress > 0) {
                const progressBar = document.createElement("div");
                progressBar.style.position = "absolute";
                progressBar.style.bottom = "0";
                progressBar.style.left = "0";
                progressBar.style.height = "2px";
                progressBar.style.backgroundColor = "rgba(255,255,255,0.8)";
                progressBar.style.width = `${progress}%`;
                progressBar.style.borderRadius = "0 0 6px 6px";
                info.el.appendChild(progressBar);
            }

            // Priority indicator
            if (props.priority === 'high') {
                info.el.style.borderTop = "2px solid #EF4444";
            } else if (props.priority === 'low') {
                info.el.style.borderTop = "2px solid #10B981";
            }

            // Enhanced tooltip
            const assignee = props.assignee ? ` | Assigned to: ${props.assignee.name}` : '';
            const daysRemaining = props.days_remaining !== null ? 
                (props.days_remaining < 0 ? ` | ${Math.abs(props.days_remaining)} days overdue` : 
                 props.days_remaining === 0 ? ' | Due today' : 
                 ` | ${props.days_remaining} days remaining`) : '';
            
            info.el.title = `${event.title} | ${props.project} | Progress: ${progress}%${assignee}${daysRemaining}`;
        },

        eventClick: info => showTaskModal(info.event),

        // Date click to show tasks for that day
        dateClick: info => showDayTasks(info.date, info.dayEl),

        locale: 'en',
        firstDay: 1,
        eventTimeFormat: { hour: 'numeric', minute: '2-digit', omitZeroMinute: true },

        // Loading state
        loading: function(isLoading) {
            const loadingEl = document.getElementById('calendar-loading');
            if (loadingEl) {
                loadingEl.style.display = isLoading ? 'block' : 'none';
            }
        }
    });

    window.dashboardCalendar.render();

    // Make responsive
    window.addEventListener('resize', () => {
        if (window.dashboardCalendar) window.dashboardCalendar.updateSize();
    });

    console.log("Calendar initialized");
}

function generateCalendarEvents(projects, projectColors) {
    const events = [];
    
    projects.forEach(project => {
        const projectName = project.project_name || project.name || "Unknown Project";
        const projectColor = projectColors[projectName] || "#6B7280";
        
        if (project.tasks && Array.isArray(project.tasks)) {
            project.tasks.forEach(task => {
                if (!task.start) return;
                
                const event = {
                    id: `task_${task.id}`,
                    title: task.title || "Untitled Task",
                    start: task.start,
                    end: task.end || null,
                    allDay: true,
                    color: projectColor,
                    borderColor: projectColor,
                    textColor: "#FFFFFF",
                    extendedProps: {
                        progress: task.progress || 0,
                        project: projectName,
                        projectId: project.id,
                        taskId: task.id,
                        description: task.description || "",
                        priority: task.priority || "normal",
                        status: task.status || "pending",
                        is_overdue: task.is_overdue || false,
                        days_remaining: task.days_remaining,
                        assignee: task.assignee || null,
                        weight: task.weight || 0,
                        manhours: task.manhours || 0,
                        scope: task.scope || null,
                        updated_at: task.updated_at
                    }
                };
                
                events.push(event);
            });
        }
    });
    
    return events;
}

function showDayTasks(date, dayEl) {
    if (!window.dashboardCalendar) return;
    
    const tasks = window.dashboardCalendar.getEvents().filter(event => {
        const eventDate = new Date(event.start);
        return eventDate.toDateString() === date.toDateString();
    });
    
    if (tasks.length === 0) return;
    
    // Create day tasks popup
    const popup = document.createElement('div');
    popup.className = 'absolute bg-white border border-gray-200 rounded-lg shadow-lg p-4 z-50 min-w-64 max-w-80';
    popup.style.top = '100%';
    popup.style.left = '0';
    popup.style.marginTop = '5px';
    
    const tasksList = tasks.map(task => {
        const props = task.extendedProps;
        const statusIcon = props.is_overdue ? '🔴' : 
                          props.status === 'completed' || props.status === 'CP' ? '✅' : 
                          props.status === 'in_progress' || props.status === 'IP' ? '🟡' : '⚪';
        
        return `
            <div class="flex items-center space-x-2 p-2 hover:bg-gray-50 rounded cursor-pointer" onclick="showTaskModal(window.dashboardCalendar.getEventById('${task.id}'))">
                <span>${statusIcon}</span>
                <div class="flex-1">
                    <div class="font-medium text-sm">${task.title}</div>
                    <div class="text-xs text-gray-500">${props.project} • ${props.progress}%</div>
                </div>
            </div>
        `;
    }).join('');
    
    popup.innerHTML = `
        <div class="flex items-center justify-between mb-3">
            <h3 class="font-semibold text-gray-900">${date.toLocaleDateString()} Tasks</h3>
            <button onclick="this.parentElement.parentElement.remove()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        </div>
        ${tasksList}
    `;
    
    // Position relative to day cell
    dayEl.style.position = 'relative';
    dayEl.appendChild(popup);
    
    // Close when clicking outside
    setTimeout(() => {
        document.addEventListener('click', function closePopup(e) {
            if (!popup.contains(e.target)) {
                popup.remove();
                document.removeEventListener('click', closePopup);
            }
        });
    }, 100);
}

// ====================================================================
// PROJECT MAP FUNCTIONALITY
// ====================================================================

let projectMap = null;
let projectMarkers = [];

// Expose projectMarkers globally for filtering
window.projectMarkers = projectMarkers;

// Philippines bounds and center
const philippinesCenter = [12.8797, 121.7740];
const philippinesBounds = [
    [4.5, 116.0],  // Southwest
    [21.5, 127.0]  // Northeast
];

// Project status colors
// Align marker colors with status card colors in the dashboard template
const statusColors = {
    'PL': '#f59e0b', // amber/yellow - Planned
    'OG': '#3b82f6', // blue - Ongoing/Active
    'IP': '#3b82f6', // blue - In Progress (same as OG)
    'CP': '#10b981', // green - Completed
    'CN': '#ef4444'  // red - Cancelled
};

function initializeProjectMap() {
    console.log('🗺️ Initializing project map...');
    console.log('🔍 DEBUG: Current window.projectMap:', window.projectMap);
    console.log('🔍 DEBUG: Is window.projectMap a Leaflet map?', !!(window.projectMap && window.projectMap._container));
    console.log('🔍 DEBUG: Leaflet available:', typeof L !== 'undefined');

    const mapContainer = document.getElementById('projectMap');
    console.log('🔍 DEBUG: Map container found:', !!mapContainer);
    if (mapContainer) {
        console.log('🔍 DEBUG: Map container dimensions:', {
            width: mapContainer.offsetWidth,
            height: mapContainer.offsetHeight,
            display: window.getComputedStyle(mapContainer).display
        });
    }

    if (!mapContainer) {
        console.warn('❌ Map container not found');
        return;
    }

    // Check if Leaflet is loaded
    if (typeof L === 'undefined') {
        console.error('❌ Leaflet library not loaded. Retrying in 1 second...');
        setTimeout(initializeProjectMap, 1000);
        return;
    }

    // Check if map is already initialized (check if it's a Leaflet map object)
    if (window.projectMap && window.projectMap._container) {
        console.log('⚠️ Map already initialized, skipping...');
        return;
    }

    try {
        // Remove existing map if it exists
        if (projectMap && projectMap._container) {
            projectMap.remove();
            projectMap = null;
        }
        
        // Clear any incorrect window.projectMap assignment
        if (window.projectMap && !window.projectMap._container) {
            console.log('🔍 DEBUG: Clearing incorrect window.projectMap assignment');
            window.projectMap = null;
        }

        // Remove loading overlay first
        const loadingEl = document.getElementById('mapLoading');
        console.log('🔍 DEBUG: Loading overlay element found:', !!loadingEl);
        if (loadingEl) {
            console.log('🔍 DEBUG: Loading overlay before removal:', {
                display: loadingEl.style.display,
                opacity: loadingEl.style.opacity,
                zIndex: loadingEl.style.zIndex,
                visibility: window.getComputedStyle(loadingEl).visibility
            });
            
            loadingEl.style.display = 'none';
            loadingEl.style.pointerEvents = 'none';
            loadingEl.style.opacity = '0';
            loadingEl.style.zIndex = '-1';
            loadingEl.remove();
            console.log('✅ Loading overlay removed');
        } else {
            console.log('⚠️ No loading overlay found to remove');
        }

        // Ensure container has proper dimensions
        mapContainer.innerHTML = '';
        mapContainer.style.height = '100%';
        mapContainer.style.width = '100%';
        mapContainer.style.position = 'relative';
        mapContainer.style.zIndex = '1';

        // Initialize Leaflet map
        console.log('🔍 DEBUG: Creating Leaflet map...');
        projectMap = L.map(mapContainer, {
            center: philippinesCenter,
            zoom: 6,
            maxBounds: philippinesBounds,
            maxBoundsViscosity: 1.0,
            zoomControl: true,
            attributionControl: true,
            dragging: true,
            scrollWheelZoom: true,
            doubleClickZoom: true,
            boxZoom: true,
            keyboard: true,
            preferCanvas: true,
            fadeAnimation: true,
            zoomAnimation: true,
            markerZoomAnimation: true
        });

        console.log('🔍 DEBUG: Leaflet map created:', !!projectMap);

        // Expose map globally
        window.projectMap = projectMap;
        console.log('🔍 DEBUG: Map exposed globally:', !!window.projectMap);
        console.log('🔍 DEBUG: Map object type:', typeof window.projectMap);
        console.log('🔍 DEBUG: Map has _container property:', !!(window.projectMap && window.projectMap._container));

        // Add OpenStreetMap tiles
        console.log('🔍 DEBUG: Adding tile layer...');
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19
        }).addTo(projectMap);

        console.log('🔍 DEBUG: Tile layer added');

        // Load project markers
        console.log('🔍 DEBUG: Loading project markers...');
        loadProjectMarkers();

        // Fit map to all markers after a short delay
        setTimeout(() => {
            if (projectMap && projectMarkers.length > 0) {
                const group = new L.featureGroup(projectMarkers);
                projectMap.fitBounds(group.getBounds().pad(0.1));
                console.log('✅ Map fitted to markers');
            }
        }, 500);

        console.log('✅ Project map initialized successfully');
        
        // Debug: Check if loading overlay is still present
        setTimeout(() => {
            const remainingLoadingEl = document.getElementById('mapLoading');
            console.log('🔍 DEBUG: Loading overlay still present after map init:', !!remainingLoadingEl);
            if (remainingLoadingEl) {
                console.log('🔍 DEBUG: Loading overlay styles:', {
                    display: remainingLoadingEl.style.display,
                    opacity: remainingLoadingEl.style.opacity,
                    visibility: window.getComputedStyle(remainingLoadingEl).visibility,
                    zIndex: remainingLoadingEl.style.zIndex
                });
            }
        }, 1000);

    } catch (error) {
        console.error('❌ Failed to initialize project map:', error);
        mapContainer.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; height: 100%; background: #f3f4f6; border-radius: 12px;">
                <div style="text-align: center; color: #6b7280; padding: 20px;">
                    <div style="font-size: 48px; margin-bottom: 16px;">🗺️</div>
                    <p style="font-weight: 600; margin-bottom: 8px;">Map failed to load</p>
                    <p style="font-size: 12px; margin-bottom: 16px;">Error: ${error.message}</p>
                    <button onclick="initializeProjectMap()" style="padding: 8px 16px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px;">
                        Retry Loading Map
                    </button>
                </div>
            </div>
        `;
    }
}

function loadProjectMarkers() {
    console.log('🔍 DEBUG: loadProjectMarkers called');
    console.log('🔍 DEBUG: projectMap available:', !!projectMap);
    console.log('🔍 DEBUG: dashboardData available:', !!window.dashboardData);
    console.log('🔍 DEBUG: projects available:', !!window.dashboardData?.projects);
    
    if (!projectMap || !window.dashboardData?.projects) {
        console.log('❌ Cannot load markers - missing projectMap or dashboardData');
        return;
    }

    const projects = window.dashboardData.projects;
    console.log(`🔍 DEBUG: Loading ${projects.length} project markers`);

    // Clear existing markers
    console.log('🔍 DEBUG: Clearing existing markers:', projectMarkers.length);
    projectMarkers.forEach(marker => {
        projectMap.removeLayer(marker);
    });
    projectMarkers = [];

    let markersAdded = 0;
    projects.forEach((project, index) => {
        console.log(`🔍 DEBUG: Processing project ${index + 1}/${projects.length}:`, {
            id: project.id,
            name: project.project_name || project.name,
            gps_coordinates: project.gps_coordinates,
            has_coordinates: !!project.gps_coordinates
        });
        
        if (project.gps_coordinates) {
            try {
                const [lat, lng] = project.gps_coordinates.split(',').map(coord => parseFloat(coord.trim()));
                console.log(`🔍 DEBUG: Parsed coordinates for project ${project.id}:`, { lat, lng });
                
                if (!isNaN(lat) && !isNaN(lng)) {
                    addProjectMarker(project, lat, lng);
                    markersAdded++;
                    console.log(`✅ Added marker for project ${project.id}`);
                } else {
                    console.log(`❌ Invalid coordinates for project ${project.id}:`, { lat, lng });
                }
            } catch (error) {
                console.warn(`❌ Failed to parse coordinates for project ${project.id}:`, error);
            }
        } else {
            console.log(`⚠️ No GPS coordinates for project ${project.id}`);
        }
    });

    console.log(`🔍 DEBUG: Total markers added: ${markersAdded}`);
    console.log(`🔍 DEBUG: projectMarkers array length: ${projectMarkers.length}`);

    // Update map statistics
    updateMapStats(projects.length, projectMarkers.length, projects.filter(p => p.status === 'OG' || p.status === 'IP').length);
}

function addProjectMarker(project, lat, lng) {
    const status = project.status || 'PL';
    const color = statusColors[status] || statusColors['PL'];

    // Create custom icon
    const markerIcon = L.divIcon({
        className: 'custom-project-marker',
        html: `
            <div class="pm-marker-bubble" style="
                background-color: ${color};
                width: 20px;
                height: 20px;
                border-radius: 50%;
                border: 2px solid white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 10px;
                color: white;
                font-weight: bold;
                transform-origin: center center;
                will-change: transform;
            ">
                ${getStatusIcon(status)}
            </div>
        `,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });

    // Create marker
    const marker = L.marker([lat, lng], { icon: markerIcon }).addTo(projectMap);

    // Bind hover tooltip with professional layout (like the screenshot)
    const statusText = getStatusText(status).toUpperCase();
    const progress = Math.max(0, Math.min(100, Number(
        typeof project.actual_progress === 'number' ? project.actual_progress : (project.progress || 0)
    ) || 0));
    const locationText = project.location || '';
    const code = project.code || project.project_code || project.project_id || project.id || '';
    const projType = project.type || project.project_type || project.category || '';
    const targetCompletion = project.target_completion || project.end_date || project.completion_date || '';
    const estCost = project.estimated_cost ?? (project.budget_total && project.budget_total.estimated);

    const mapContainerEl = document.getElementById('projectMap');
    const maxTooltipWidth = mapContainerEl ? Math.max(220, Math.min(320, mapContainerEl.offsetWidth - 24)) : 320;
    const tooltipHtml = `
        <div style="min-width:220px;max-width:${maxTooltipWidth}px;padding:10px 12px;border-radius:14px;background:#ffffff;box-shadow:0 10px 26px rgba(0,0,0,.14);border:1px solid rgba(0,0,0,.06);">
            <div style="display:flex;align-items:start;justify-content:space-between;gap:12px;">
                <div style="font-weight:800;color:#111827;line-height:1.2;">${project.project_name || project.name || 'Unnamed Project'}</div>
                <div style="font-size:11px;font-weight:700;color:#6b7280;">${statusText}</div>
            </div>
            ${code ? `<div style=\"font-size:12px;color:#6b7280;margin-top:2px;\">${code}</div>` : ''}
            <div style="height:1px;background:#e5e7eb;margin:8px 0;"></div>
            ${locationText ? `<div style=\"font-size:12px;color:#111827;\">
                <span style=\"font-weight:700;\">Location:</span>
                <div style=\"color:#374151;white-space:normal;word-break:break-word;overflow-wrap:anywhere;margin-top:2px;\">${locationText}</div>
            </div>` : ''}
            ${projType ? `<div style=\"font-size:12px;color:#111827;\"><span style=\"font-weight:700;\">Type:</span> <span style=\"color:#374151;\">${projType}</span></div>` : ''}
            <div style="margin-top:6px;font-size:12px;color:#111827;">
                <span style="font-weight:700;">Progress:</span>
                <span style="color:${color};font-weight:800;"> ${progress}%</span>
                <div style="margin-top:4px;background:#e5e7eb;height:6px;border-radius:9999px;overflow:hidden;">
                    <div style="width:${progress}%;height:100%;background:${color};"></div>
                </div>
            </div>
            ${project.start_date ? `<div style=\"margin-top:6px;font-size:12px;color:#111827;\"><span style=\"font-weight:700;\">Start Date:</span> <span style=\"color:#374151;\">${formatDate(project.start_date)}</span></div>` : ''}
            ${targetCompletion ? `<div style=\"font-size:12px;color:#111827;\"><span style=\"font-weight:700;\">Target Completion:</span> <span style=\"color:#374151;\">${formatDate(targetCompletion)}</span></div>` : ''}
            ${estCost !== undefined && estCost !== null ? `<div style=\"font-size:12px;color:#111827;\"><span style=\"font-weight:700;\">Estimated Cost:</span> <span style=\"color:#374151;\">${formatCurrency(estCost)}</span></div>` : ''}
        </div>
    `;
    marker.bindTooltip(tooltipHtml, { direction: 'auto', offset: [0, -16], opacity: 0.98, sticky: true, className: 'leaflet-tooltip pm-tooltip' });

    // Add click event - navigate directly to project view
    marker.on('click', function() {
        const typeCode = getProjectTypeCode(project);
        const projectId = project.id || project.project_id;

        let href = project.view_url || project.url || null;
        if (!href && typeCode && projectId) {
            href = `/projects/view/${typeCode}/${projectId}/`;
        } else if (!href && projectId) {
            href = `/projects/${projectId}/`;
        }

        if (href) {
            window.location.href = href;
        } else {
            const center = this.getLatLng();
            showProjectPopup(project, center);
        }
    });

    // Add hover effects (scale only the inner bubble, not the marker container)
    marker.on('mouseover', function() {
        const el = this.getElement();
        if (!el) return;
        const bubble = el.querySelector('.pm-marker-bubble');
        if (bubble) bubble.style.transform = 'scale(1.2)';
        if (typeof this.bringToFront === 'function') this.bringToFront();
    });

    marker.on('mouseout', function() {
        const el = this.getElement();
        if (!el) return;
        const bubble = el.querySelector('.pm-marker-bubble');
        if (bubble) bubble.style.transform = 'scale(1)';
    });

    projectMarkers.push(marker);
    window.projectMarkers = projectMarkers;
}

function getStatusIcon(status) {
    switch(status) {
        case 'PL': return '●'; // Planned
        case 'IP': return '▶'; // In Progress
        case 'CP': return '✓'; // Completed
        case 'CN': return '✕'; // Cancelled
        default: return '●';
    }
}

function showProjectPopup(project, latlng) {
    const popup = document.getElementById('projectPopup');
    const title = document.getElementById('popupTitle');
    const content = document.getElementById('popupContent');
    const viewBtn = document.getElementById('popupViewBtn');

    if (!popup || !title || !content || !viewBtn) return;

    // Set popup content
    title.textContent = project.project_name || 'Unnamed Project';

    const statusText = getStatusText(project.status);
    const statusColor = statusColors[project.status] || statusColors['PL'];

    content.innerHTML = `
        <div class="flex items-center space-x-2 mb-2">
            <span class="w-3 h-3 rounded-full" style="background-color: ${statusColor}"></span>
            <span class="font-medium">${statusText}</span>
        </div>
        <div><strong>Location:</strong> ${project.location || 'N/A'}</div>
        <div><strong>Client:</strong> ${project.client_name || 'N/A'}</div>
        ${project.start_date ? `<div><strong>Start Date:</strong> ${formatDate(project.start_date)}</div>` : ''}
        ${project.estimated_cost ? `<div><strong>Est. Cost:</strong> ₱${parseFloat(project.estimated_cost).toLocaleString()}</div>` : ''}
    `;

    // Set view button action
    viewBtn.onclick = () => {
        if (project.view_url) {
            window.open(project.view_url, '_blank');
        }
        closeProjectPopup();
    };

    // Position popup on map
    const mapContainer = document.getElementById('projectMap');
    const point = projectMap.latLngToContainerPoint(latlng);

    popup.style.left = `${Math.min(point.x, mapContainer.offsetWidth - 320)}px`;
    popup.style.top = `${Math.max(point.y - 120, 10)}px`;
    popup.classList.remove('hidden');
}

function closeProjectPopup() {
    const popup = document.getElementById('projectPopup');
    if (popup) {
        popup.classList.add('hidden');
    }
}

function getStatusText(status) {
    switch(status) {
        case 'PL': return 'Planned';
        case 'IP': return 'Active';
        case 'OG': return 'Active';
        case 'CP': return 'Completed';
        case 'CN': return 'Cancelled';
        default: return 'Unknown';
    }
}

function formatDate(dateString) {
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch (error) {
        return dateString;
    }
}

// Currency formatter for professional tooltip display
function formatCurrency(amount) {
    const value = Number(amount);
    if (isNaN(value)) return '';
    return `₱${value.toLocaleString()}`;
}

function updateMapStats(totalProjects, mappedProjects, activeProjects) {
    const totalEl = document.getElementById('totalProjectsCount');
    const mappedEl = document.getElementById('mappedProjectsCount');
    const activeEl = document.getElementById('activeProjectsCount');

    if (totalEl) totalEl.textContent = totalProjects;
    if (mappedEl) mappedEl.textContent = mappedProjects;
    if (activeEl) activeEl.textContent = activeProjects;
}

// Derive short project type code (e.g., GC, DC, EA) from various fields
function getProjectTypeCode(project) {
    // Only two valid codes: GC and DC
    const VALID = ['GC', 'DC'];

    // 1) Explicit short code
    const explicit = (project.type_code || '').toString().trim().toUpperCase();
    if (VALID.includes(explicit)) return explicit;

    // 2) Prefix from a code like GC-001 / DC_032
    const codeLike = (project.project_code || project.code || '').toString().trim();
    const codePrefixMatch = codeLike.match(/^([A-Za-z]{2})(?:[-_\s]|\d)/);
    if (codePrefixMatch && VALID.includes(codePrefixMatch[1].toUpperCase())) {
        return codePrefixMatch[1].toUpperCase();
    }

    // 3) Keyword mapping from long names → GC or DC
    const rawType = (project.type || project.project_type || project.category || '').toString();
    const normalized = rawType.replace(/[_-]+/g, ' ').replace(/\s+/g, ' ').trim().toUpperCase();

    if (/(GENERAL\s+(CONTRACT(ING|OR|ION)?|CONSTRUCTION))/.test(normalized)) return 'GC';
    if (/(DESIGN|CONSTRUCT|BUILD|RESIDENTIAL|COMMERCIAL)/.test(normalized)) return 'DC';

    // 4) Default: if nothing matches, prefer DC
    return 'DC';
}

// ====================================================================
// TASK MODAL FUNCTIONALITY
// ====================================================================

function showTaskModal(event) {
    const modal = document.getElementById("taskModal");
    const modalTitle = document.getElementById("modalTitle");
    const modalBody = document.getElementById("modalBody");
    
    if (!modal || !modalTitle || !modalBody) {
        console.error("Modal elements not found");
        return;
    }
    
    const title = event.title;
    const props = event.extendedProps;
    const project = props.project;
    const progress = props.progress || 0;
    const startDate = event.start;
    const endDate = event.end;
    const description = props.description || "No description available";
    const priority = props.priority || "normal";
    const assignee = props.assignee;
    const weight = props.weight || 0;
    const manhours = props.manhours || 0;
    const scope = props.scope;
    
    const formatDate = (date) => {
        if (!date) return "Not set";
        return date.toLocaleDateString('en-US', {
            weekday: 'short',
            year: 'numeric', 
            month: 'short',
            day: 'numeric'
        });
    };
    
    const getDuration = () => {
        if (!startDate || !endDate) return "Not specified";
        const diffTime = Math.abs(endDate - startDate);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return diffDays === 1 ? "1 day" : `${diffDays} days`;
    };
    
    const getProgressColor = (progress) => {
        if (progress >= 100) return "bg-green-500";
        if (progress >= 75) return "bg-blue-500";
        if (progress >= 50) return "bg-yellow-500";
        if (progress >= 25) return "bg-orange-500";
        return "bg-red-500";
    };
    
    const getPriorityBadge = (priority) => {
        const colors = {
            high: "bg-red-100 text-red-800 border border-red-200",
            medium: "bg-yellow-100 text-yellow-800 border border-yellow-200", 
            low: "bg-green-100 text-green-800 border border-green-200",
            normal: "bg-gray-100 text-gray-800 border border-gray-200"
        };
        return `<span class="px-3 py-1 text-xs rounded-full font-medium ${colors[priority] || colors.normal}">${priority.toUpperCase()}</span>`;
    };
    
    modalTitle.textContent = title;
    modalBody.innerHTML = `
    <div class="space-y-4">
        <!-- Header Row -->
        <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div class="flex items-center space-x-2">
                <div class="w-3 h-3 rounded-full bg-blue-500"></div>
                <span class="text-sm font-medium text-gray-600">Project:</span>
                <span class="font-semibold text-gray-900">${project}</span>
            </div>
            ${getPriorityBadge(priority)}
        </div>

        <!-- Progress and Dates Row -->
        <div class="grid grid-cols-3 gap-4">
            <div class="text-center p-3 bg-gray-50 rounded-lg">
                <p class="text-xs text-gray-500 mb-1">Progress</p>
                <p class="text-xl font-bold text-gray-900 mb-2">${progress}%</p>
                <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="${getProgressColor(progress)} h-2 rounded-full transition-all duration-500" 
                         style="width: ${progress}%"></div>
                </div>
            </div>
            <div class="p-3 border border-gray-200 rounded-lg">
                <div class="flex items-center space-x-1 mb-1">
                    <i class="fas fa-play text-green-500 text-xs"></i>
                    <span class="text-xs font-medium text-gray-600">Start</span>
                </div>
                <p class="text-sm font-semibold text-gray-900">${formatDate(startDate)}</p>
            </div>
            <div class="p-3 border border-gray-200 rounded-lg">
                <div class="flex items-center space-x-1 mb-1">
                    <i class="fas fa-flag-checkered text-red-500 text-xs"></i>
                    <span class="text-xs font-medium text-gray-600">End</span>
                </div>
                <p class="text-sm font-semibold text-gray-900">${formatDate(endDate)}</p>
            </div>
        </div>

        <!-- Details Row -->
        <div class="grid grid-cols-${assignee ? '2' : '1'} gap-4">
            ${assignee ? `
            <div class="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div class="flex items-center space-x-2">
                    <div class="w-8 h-8 rounded-full bg-gradient-to-r from-blue-400 to-purple-500 flex items-center justify-center text-white font-semibold text-sm flex-shrink-0">
                        ${assignee.name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                        <p class="text-sm font-semibold text-gray-900">${assignee.name}</p>
                        <p class="text-xs text-gray-500">${assignee.email}</p>
                    </div>
                </div>
            </div>
            ` : ''}
            
            <div class="grid grid-cols-3 gap-2">
                <div class="text-center p-2 bg-gray-50 rounded">
                    <p class="text-xs text-gray-500">Weight</p>
                    <p class="text-sm font-semibold text-gray-900">${weight}%</p>
                </div>
                <div class="text-center p-2 bg-gray-50 rounded">
                    <p class="text-xs text-gray-500">Hours</p>
                    <p class="text-sm font-semibold text-gray-900">${manhours}h</p>
                </div>
                <div class="text-center p-2 bg-gray-50 rounded">
                    <p class="text-xs text-gray-500">Duration</p>
                    <p class="text-sm font-semibold text-gray-900">${getDuration()}</p>
                </div>
            </div>
        </div>

        ${scope ? `
        <div class="p-2 bg-purple-50 border border-purple-200 rounded-lg">
            <span class="text-xs font-medium text-purple-600">Scope: </span>
            <span class="text-sm font-semibold text-purple-900">${scope.name}</span>
        </div>
        ` : ''}
        
        ${description && description !== "No description available" ? `
        <div class="p-3 bg-gray-50 rounded-lg border-l-4 border-blue-500">
            <p class="text-xs font-medium text-gray-600 mb-1">Description</p>
            <p class="text-sm text-gray-700 leading-relaxed">${description}</p>
        </div>
        ` : ''}

        <!-- Footer Row -->
        <div class="flex items-center justify-between pt-3 border-t">
            <div class="flex space-x-4 text-xs text-gray-500">
                ${props.days_remaining !== null ? 
                    props.days_remaining < 0 ? `<span class="text-red-500 font-medium">${Math.abs(props.days_remaining)} days overdue</span>` :
                    props.days_remaining === 0 ? '<span class="text-yellow-500 font-medium">Due today</span>' :
                    `<span>${props.days_remaining} days remaining</span>` : ''
                }
            </div>
            <div class="flex space-x-2">
                <button onclick="closeTaskModal()" class="px-3 py-1 bg-gray-200 text-gray-800 text-sm rounded hover:bg-gray-300">Close</button>
                <a href="/projects/${props.projectId}/tasks/${props.taskId}/" class="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">Details</a>
            </div>
        </div>
    </div>
`;
    
    modal.classList.remove("hidden");
    const modalContent = document.getElementById("modalContent");
    if (modalContent) {
        setTimeout(() => {
            modalContent.style.opacity = '1';
            modalContent.style.transform = 'scale(1)';
        }, 10);
    }
}

function closeTaskModal() {
    const modal = document.getElementById("taskModal");
    const modalContent = document.getElementById("modalContent");
    
    if (modalContent) {
        modalContent.style.opacity = '0';
        modalContent.style.transform = 'scale(0.95)';
    }
    
    setTimeout(() => {
        if (modal) modal.classList.add("hidden");
    }, 300);
}

// ====================================================================
// INTERACTIONS & FILTERING
// ====================================================================

function initializeInteractions() {
    initializeStatusCardFilters();
    initializeSearchFeatures();
    initializeModalEventListeners();
}

function initializeStatusCardFilters() {
    const filterCards = document.querySelectorAll('.filter-card');
    let activeFilter = null;
    
    filterCards.forEach(card => {
        card.addEventListener('click', function() {
            const status = this.dataset.status;
            
            if (activeFilter === status) {
                activeFilter = null;
                filterCards.forEach(c => {
                    c.classList.remove('ring-4', 'ring-blue-300', 'ring-opacity-50');
                    c.style.transform = 'scale(1)';
                });
                showAllProjects();
                if (typeof window.filterMapByStatus === 'function') {
                    window.filterMapByStatus(null);
                }
            } else {
                activeFilter = status;
                
                filterCards.forEach(c => {
                    c.classList.remove('ring-4', 'ring-blue-300', 'ring-opacity-50');
                    c.style.transform = 'scale(1)';
                });
                
                this.classList.add('ring-4', 'ring-blue-300', 'ring-opacity-50');
                this.style.transform = 'scale(1.02)';
                
                filterProjectsByStatus(status);
                if (typeof window.filterMapByStatus === 'function') {
                    window.filterMapByStatus(status);
                }
            }
        });
    });
}

function filterProjectsByStatus(status) {
    if (!window.dashboardData?.projects) return;
    
    const filteredProjects = window.dashboardData.projects.filter(project => {
        const projectStatus = project.status || 'PL';
        return projectStatus === status;
    });
    
    updateChartsWithFilteredData(filteredProjects);
    updateCalendarWithFilteredData(filteredProjects);
    updateMapMarkersWithFilteredData(filteredProjects);
    showFilterIndicator(status, filteredProjects.length);
}

// Expose a simple helper so other scripts can trigger map-only filtering
// Pass null to clear filter and show all markers
window.filterMapByStatus = function(status) {
    if (!window.dashboardData?.projects) return;
    if (!projectMap) return;

    if (!status) {
        updateMapMarkersWithFilteredData(window.dashboardData.projects);
        return;
    }

    const filtered = window.dashboardData.projects.filter(p => (p.status || 'PL') === status);
    updateMapMarkersWithFilteredData(filtered);
};

function showAllProjects() {
    if (!window.dashboardData?.projects) return;
    
    updateChartsWithFilteredData(window.dashboardData.projects);
    updateCalendarWithFilteredData(window.dashboardData.projects);
    updateMapMarkersWithFilteredData(window.dashboardData.projects);
    hideFilterIndicator();
}

function updateChartsWithFilteredData(projects) {
    // Progress Chart
    if (window.progressChart) {
        window.progressChart.data.labels = projects.map(p => p.name || p.project_name);
        window.progressChart.data.datasets[0].data = projects.map(p => p.planned_progress || 0);
        window.progressChart.data.datasets[1].data = projects.map(p => p.actual_progress || 0);
        window.progressChart.update('active');
    }

    // Budget Chart
    if (window.budgetChart) {
        window.budgetChart.data.labels = projects.map(p => p.name || p.project_name);
        window.budgetChart.data.datasets[0].data = projects.map(p => p.budget_total?.estimated || 0);
        window.budgetChart.data.datasets[1].data = projects.map(p => p.budget_total?.approved || 0);
        window.budgetChart.data.datasets[2].data = projects.map(p => p.budget_total?.planned || 0);
        window.budgetChart.data.datasets[3].data = projects.map(p => p.budget_total?.allocated || 0);
        window.budgetChart.data.datasets[4].data = projects.map(p => p.budget_total?.spent || 0);
        window.budgetChart.update('active');
    }
}

function updateCalendarWithFilteredData(projects) {
    if (!window.dashboardCalendar) return;

    const projectColors = generateProjectColors(projects);
    const events = generateCalendarEvents(projects, projectColors);

    window.dashboardCalendar.removeAllEvents();
    window.dashboardCalendar.addEventSource(events);
}

function updateMapMarkersWithFilteredData(projects) {
    if (!projectMap) return;

    // Clear existing markers
    projectMarkers.forEach(marker => {
        projectMap.removeLayer(marker);
    });
    projectMarkers = [];

    // Add markers for filtered projects
    projects.forEach(project => {
        if (project.gps_coordinates) {
            try {
                const [lat, lng] = project.gps_coordinates.split(',').map(coord => parseFloat(coord.trim()));
                if (!isNaN(lat) && !isNaN(lng)) {
                    addProjectMarker(project, lat, lng);
                }
            } catch (error) {
                console.warn(`Failed to parse coordinates for project ${project.id}:`, error);
            }
        }
    });

    // Refit map to current markers if any
    try {
        if (projectMarkers.length > 0) {
            const group = new L.featureGroup(projectMarkers);
            projectMap.fitBounds(group.getBounds().pad(0.15));
        }
    } catch (e) {
        console.warn('Failed to fit bounds to filtered markers:', e);
    }

    // Update map statistics
    updateMapStats(projects.length, projectMarkers.length, projects.filter(p => p.status === 'OG' || p.status === 'IP').length);
}

function showFilterIndicator(status, count) {
    const statusNames = {
        'PL': 'Planned',
        'OG': 'Active', 
        'CP': 'Completed',
        'CN': 'Discontinued'
    };
    
    let indicator = document.getElementById('filterIndicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'filterIndicator';
        indicator.className = 'fixed top-20 right-4 bg-blue-500 text-white px-4 py-2 rounded-lg shadow-lg z-40 transition-all duration-300';
        document.body.appendChild(indicator);
    }
    
    indicator.innerHTML = `
        <div class="flex items-center space-x-2">
            <i class="fas fa-filter"></i>
            <span>Showing ${statusNames[status]} (${count})</span>
            <button onclick="showAllProjects()" class="ml-2 text-white hover:text-gray-200">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    indicator.style.opacity = '1';
    indicator.style.transform = 'translateX(0)';
}

function hideFilterIndicator() {
    const indicator = document.getElementById('filterIndicator');
    if (indicator) {
        indicator.style.opacity = '0';
        indicator.style.transform = 'translateX(100%)';
        setTimeout(() => indicator.remove(), 300);
    }
}

function initializeSearchFeatures() {
    const searchInput = document.getElementById('projectSearch');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleSearch, 300));
    }
}

function handleSearch(event) {
    const query = event.target.value.toLowerCase().trim();
    
    if (!query) {
        showAllProjects();
        return;
    }
    
    const filteredProjects = window.dashboardData.projects.filter(project =>
        (project.name || project.project_name || '').toLowerCase().includes(query) ||
        (project.description && project.description.toLowerCase().includes(query))
    );
    
    updateChartsWithFilteredData(filteredProjects);
    updateCalendarWithFilteredData(filteredProjects);
    updateMapMarkersWithFilteredData(filteredProjects);
    showFilterIndicator('Search', filteredProjects.length);
}

function initializeModalEventListeners() {
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal-backdrop') || 
            e.target.id === 'taskModal') {
            closeTaskModal();
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeTaskModal();
        }
    });
}

// ====================================================================
// GLOBAL EXPORTS
// ====================================================================

// Global functions for template use
window.closeTaskModal = closeTaskModal;
window.showAllProjects = showAllProjects;
window.filterProjectsByStatus = filterProjectsByStatus;
window.closeProjectPopup = closeProjectPopup;

// Utility exports
window.dashboardUtils = {
    showAllProjects,
    filterProjectsByStatus,
    showSuccessMessage,
    showErrorMessage,
    showInfoMessage,
    closeTaskModal,
    closeProjectPopup
};

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.progressChart) {
        window.progressChart.destroy();
    }
    if (window.budgetChart) {
        window.budgetChart.destroy();
    }
    if (window.dashboardCalendar) {
        window.dashboardCalendar.destroy();
    }
    
    console.log('Essential Dashboard cleanup completed');
});

console.log('Essential Dashboard script loaded successfully!');
