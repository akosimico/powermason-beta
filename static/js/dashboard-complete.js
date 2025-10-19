// dashboard-complete.js - Enhanced Dashboard JavaScript with Real-time Task Updates

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

function animateElements() {
    const animatedElements = document.querySelectorAll('.animate-fade-in, .animate-slide-up');
    animatedElements.forEach((el, index) => {
        setTimeout(() => {
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, index * 100);
    });
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

function showMinimalistToast(message, type = 'success') {
    // Remove any existing minimalist toasts
    const existing = document.querySelectorAll('.minimalist-toast');
    existing.forEach(el => el.remove());

    const toast = document.createElement('div');
    toast.className = 'minimalist-toast fixed top-6 right-6 bg-white/90 backdrop-blur-xl text-gray-800 px-4 py-2 rounded-full shadow-lg z-50 transition-all duration-700 transform translate-y-[-20px] opacity-0 border border-green-200';

    const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
    toast.innerHTML = `
        <div class="flex items-center space-x-2">
            <span class="text-green-600 font-bold">${icon}</span>
            <span class="text-sm font-medium">${message}</span>
        </div>
    `;

    document.body.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        toast.style.transform = 'translateY(0)';
        toast.style.opacity = '1';
    });

    // Auto-dismiss after 1.5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.transform = 'translateY(-20px)';
            toast.style.opacity = '0';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, 700);
        }
    }, 1500);
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
    // Inline map disabled - using modal map instead
}

let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(handleResize, 250);
});

window.addEventListener('error', function(e) {
    console.error('Dashboard error:', e.error);
    showErrorMessage('Something went wrong. Please refresh if issues persist.');
});

window.addEventListener('load', () => {
    if (window.performance) {
        const perfData = window.performance.timing;
        const loadTime = perfData.loadEventEnd - perfData.navigationStart;
        console.log(`Dashboard loaded in ${loadTime}ms`);
    }
});

// ====================================================================
// MAIN DASHBOARD INITIALIZATION
// ====================================================================

document.addEventListener("DOMContentLoaded", () => {
    console.log("Dashboard loading...");

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

    // Initialize all components
    initializeDashboard();
});

function initializeDashboard() {
    try {
        // Session-based dashboard - no tokens needed
        console.log('Initializing session-based dashboard');

        // Initialize components in order
        initializeCharts();
        initializeCalendar();

        // Initialize inline map for better user experience
        console.log('🗺️ Initializing inline map...');

        // Map initialization is handled by inline script in dashboard.html template
        // This prevents conflicts between multiple map initialization systems
        console.log('🗺️ Map initialization deferred to template inline script');

        // Wait for template map to be ready, then connect filtering and fix interactions
        setTimeout(() => {
            if (window.projectMap && window.filterMapByStatus) {
                console.log('✅ Template map detected, connecting dashboard filtering');
                // Map filtering will work through the template's filterMapByStatus function

                // Force enable interactions after template map loads
                setTimeout(() => {
                    forceEnableMapInteractions();
                }, 500);
            } else {
                console.log('⚠️ Template map not found, falling back to dashboard-complete.js implementation');
                tryLeafletInitialization();
            }
        }, 1000);

        function tryLeafletInitialization() {
            try {
                window.initializeprojectMap();
                console.log('✅ Leaflet map initialized successfully');
            } catch (error) {
                console.error('❌ Failed to initialize Leaflet map:', error);
                console.log('⚠️ Using modal-based map viewer only');
            }
        }

        initializeInteractions();
        initializeModals();

        // DISABLED: Auto-refresh causing issues
        // Start auto-refresh after everything is loaded (only if on dashboard)
        // if (window.location.pathname.includes('/dashboard/')) {
        //     setTimeout(() => {
        //         initializeAutoRefresh();
        //     }, 1500);
        // }

        // Add loading states and animations
        hideLoadingOverlay();
        animateElements();

        // Dashboard loaded successfully - no message needed

        console.log("Dashboard initialized successfully");

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

    // dataset[0] = Planned Progress, dataset[1] = Actual Progress
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
// ENHANCED CALENDAR FUNCTIONALITY  
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

    console.log("Enhanced calendar initialized");
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
// ENHANCED MODAL FUNCTIONALITY
// ====================================================================

function initializeModals() {
    setupModalEventListeners();
    console.log('Modal system initialized');
}

function setupModalEventListeners() {
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
// ENHANCED AUTO-REFRESH FUNCTIONALITY
// ====================================================================

function initializeAutoRefresh() {
    window.dashboardAutoRefresh = new DashboardAutoRefresh({
        interval: 30000, // 30 seconds
        apiEndpoint: '/api/dashboard/'
    });
}

class DashboardAutoRefresh {
    constructor(options = {}) {
        this.refreshInterval = options.interval || 30000;
        this.apiEndpoint = options.apiEndpoint || '/api/dashboard/';
        this.isActive = true;
        this.retryCount = 0;
        this.maxRetries = 3;
        this.intervalId = null;
        this.lastUpdateTimestamp = null;
        
        this.init();
    }

    init() {
        console.log('Auto-refresh initialized (30s interval)');
        this.startAutoRefresh();
        this.addEventListeners();
        this.showConnectionStatus('Auto-refresh active');
        this.lastUpdateTimestamp = window.dashboardData.timestamp;
    }

    startAutoRefresh() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }

        this.intervalId = setInterval(() => {
            if (this.isActive && !document.hidden) {
                this.fetchAndUpdate();
            }
        }, this.refreshInterval);

        console.log(`Auto-refresh started (${this.refreshInterval / 1000}s interval)`);
    }

    async fetchAndUpdate() {
        try {
            // Show minimalist updating notification
            this.showMinimalistNotification('Updating...');

            // Use session-based API endpoint
            const response = await fetch(
                `/api/dashboard/`,
                {
                    method: 'GET',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Content-Type': 'application/json',
                        'Cache-Control': 'no-cache'
                    },
                    credentials: 'same-origin',
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success) {
                const hasChanges = this.detectAndHandleChanges(data);

                if (hasChanges) {
                    this.updateDashboard(data);
                    this.lastUpdateTimestamp = data.timestamp;
                    this.showMinimalistNotification('Updated', 'success');
                } else {
                    // Quietly remove updating notification
                    this.hideMinimalistNotification();
                }
                this.retryCount = 0;
            } else {
                throw new Error(data.message || 'Unknown error');
            }

        } catch (error) {
            console.error('Auto-refresh failed:', error);
            this.handleError(error);
        }
    }

    detectAndHandleChanges(newData) {
        // Check if this is the first update
        if (!this.lastUpdateTimestamp) {
            return true;
        }

        // Compare timestamps first
        if (newData.timestamp !== this.lastUpdateTimestamp) {
            return true;
        }

        // Compare project counts and project IDs
        const currentProjects = window.dashboardData?.projects || [];
        const newProjects = newData.projects || [];

        // Check if project count changed
        if (currentProjects.length !== newProjects.length) {
            console.log('Project count changed:', currentProjects.length, '→', newProjects.length);
            return true;
        }

        // Check if project IDs changed (projects added/removed)
        const currentIds = new Set(currentProjects.map(p => p.id));
        const newIds = new Set(newProjects.map(p => p.id));

        const addedProjects = [...newIds].filter(id => !currentIds.has(id));
        const removedProjects = [...currentIds].filter(id => !newIds.has(id));

        if (addedProjects.length > 0 || removedProjects.length > 0) {
            console.log('Projects changed - Added:', addedProjects, 'Removed:', removedProjects);
            return true;
        }

        // Check for significant data changes (status, progress, location, etc.)
        for (const newProject of newProjects) {
            const currentProject = currentProjects.find(p => p.id === newProject.id);
            if (currentProject) {
                // Check key fields for changes
                const fieldsToCheck = ['status', 'progress', 'location', 'gps_coordinates', 'city_province'];
                for (const field of fieldsToCheck) {
                    if (currentProject[field] !== newProject[field]) {
                        console.log(`Project ${newProject.id} ${field} changed:`, currentProject[field], '→', newProject[field]);
                        return true;
                    }
                }
            }
        }

        return false;
    }

    // ... rest of the class methods remain the same
    updateDashboard(data) {
        // Update status counts with animation
        if (data.status_counts) {
            this.animateStatusCards(data.status_counts);
        }

        // Update task status counts if available
        if (data.task_status_counts) {
            this.updateTaskStatusCounts(data.task_status_counts);
        }

        // Update global dashboard data
        if (data.projects) {
            window.dashboardData = {
                projects: data.projects,
                timestamp: data.timestamp,
                metrics: data.metrics,
                status_counts: data.status_counts,
                task_status_counts: data.task_status_counts
            };
            this.updateCharts(data.projects);
            this.updateCalendar(data.projects);

            // Update map markers if available
            this.updateProjectMap(data.projects);
        }

    }

    animateStatusCards(statusCounts) {
        const cardSelectors = {
            planned: '[data-status="PL"] .text-3xl',
            ongoing: '[data-status="OG"] .text-3xl',
            completed: '[data-status="CP"] .text-3xl',
            cancelled: '[data-status="CN"] .text-3xl'
        };

        Object.entries(statusCounts).forEach(([status, count]) => {
            const element = document.querySelector(cardSelectors[status]);
            if (element) {
                const currentValue = parseInt(element.textContent) || 0;
                const newValue = parseInt(count) || 0;

                if (currentValue !== newValue) {
                    element.style.transform = 'scale(1.15)';
                    element.style.transition = 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)';
                    
                    const card = element.closest('.filter-card');
                    if (card) {
                        card.style.boxShadow = '0 0 20px rgba(59, 130, 246, 0.5)';
                    }
                    
                    setTimeout(() => {
                        element.textContent = newValue;
                        element.style.transform = 'scale(1)';
                        
                        if (card) {
                            card.style.boxShadow = '';
                        }
                    }, 200);
                }
            }
        });
    }

    updateTaskStatusCounts(taskStatusCounts) {
        // Update task metrics display if elements exist
        const elements = {
            total: document.querySelector('[data-task-metric="total"]'),
            completed: document.querySelector('[data-task-metric="completed"]'),
            in_progress: document.querySelector('[data-task-metric="in_progress"]'),
            pending: document.querySelector('[data-task-metric="pending"]'),
            overdue: document.querySelector('[data-task-metric="overdue"]')
        };

        Object.entries(taskStatusCounts).forEach(([status, count]) => {
            const element = elements[status];
            if (element) {
                const currentValue = parseInt(element.textContent) || 0;
                if (currentValue !== count) {
                    element.textContent = count;
                    element.style.transform = 'scale(1.1)';
                    element.style.transition = 'transform 0.3s ease';
                    setTimeout(() => {
                        element.style.transform = 'scale(1)';
                    }, 300);
                }
            }
        });
    }

    updateCharts(projects) {
        // Update progress chart
        if (window.progressChart) {
            const labels = projects.map(p => p.name || p.project_name);
            const plannedData = projects.map(p => p.planned_progress || 0);
            const actualData = projects.map(p => p.actual_progress || 0);
            
            const hasChanged = JSON.stringify(window.progressChart.data.labels) !== JSON.stringify(labels);
            
            if (hasChanged) {
                window.progressChart.data.labels = labels;
                window.progressChart.data.datasets[0].data = plannedData;
                window.progressChart.data.datasets[1].data = actualData;
                window.progressChart.update('none');
            }
        }

        // Update budget chart
        if (window.budgetChart) {
            const labels = projects.map(p => p.name || p.project_name);
            const estimatedBudget = projects.map(p => p.budget_total?.estimated || 0);
            const approvedBudget = projects.map(p => p.budget_total?.approved || 0);
            const plannedBudget = projects.map(p => p.budget_total?.planned || 0);
            const allocatedBudget = projects.map(p => p.budget_total?.allocated || 0);
            const spentBudget = projects.map(p => p.budget_total?.spent || 0);

            const hasChanged = JSON.stringify(window.budgetChart.data.labels) !== JSON.stringify(labels);

            if (hasChanged) {
                window.budgetChart.data.labels = labels;
                window.budgetChart.data.datasets[0].data = estimatedBudget;
                window.budgetChart.data.datasets[1].data = approvedBudget;
                window.budgetChart.data.datasets[2].data = plannedBudget;
                window.budgetChart.data.datasets[3].data = allocatedBudget;
                window.budgetChart.data.datasets[4].data = spentBudget;
                window.budgetChart.update('none');
            }
        }
    }

    updateCalendar(projects) {
        if (!window.dashboardCalendar) return;

        const projectColors = generateProjectColors(projects);
        const events = generateCalendarEvents(projects, projectColors);

        // Only update if events have changed
        const currentEventIds = window.dashboardCalendar.getEvents().map(e => e.id).sort();
        const newEventIds = events.map(e => e.id).sort();

        if (JSON.stringify(currentEventIds) !== JSON.stringify(newEventIds)) {
            window.dashboardCalendar.removeAllEvents();
            window.dashboardCalendar.addEventSource(events);
        }
    }

    updateProjectMap(projects) {
        // Clear existing markers first
        this.clearAllMapMarkers();

        // Update Mapbox map first (modern approach)
        if (window.map && window.map.getSource) {
            this.updateMapboxMap(projects);
        }
        // Fallback to Leaflet if it exists
        else if (window.projectMap) {
            this.updateLeafletMap(projects);
        }

        // Force a map refresh/redraw
        setTimeout(() => {
            if (window.map && window.map.resize) {
                window.map.resize();
            }
            if (window.projectMap && window.projectMap.invalidateSize) {
                window.projectMap.invalidateSize();
            }
        }, 100);
    }

    updateLeafletMap(projects) {
        try {
            console.log('Updating Leaflet project map markers...');

            // Ensure map is draggable
            if (window.projectMap.dragging && !window.projectMap.dragging.enabled()) {
                window.projectMap.dragging.enable();
            }
            if (window.projectMap.scrollWheelZoom && !window.projectMap.scrollWheelZoom.enabled()) {
                window.projectMap.scrollWheelZoom.enable();
            }

            // Update markers with current project data using smart system
            if (window.filterMapByStatus && typeof window.filterMapByStatus === 'function') {
                console.log('🗺️ Using template map system for auto-refresh marker update');
                // Template map handles its own markers, don't interfere
            } else if (typeof window.loadProjectMarkers === 'function') {
                console.log('🗺️ Using dashboard-complete.js smart marker system for auto-refresh');
                window.loadProjectMarkers();
            } else {
                // Fallback: add markers directly
                this.addLeafletMarkers(projects);
            }
        } catch (error) {
            console.warn('Failed to update Leaflet map:', error);
        }
    }

    updateMapboxMap(projects) {
        try {
            console.log('Updating Mapbox map markers...');

            // Ensure Mapbox map is draggable and all interactions are enabled
            if (!window.map.dragPan.isEnabled()) {
                window.map.dragPan.enable();
            }
            if (!window.map.scrollZoom.isEnabled()) {
                window.map.scrollZoom.enable();
            }
            if (!window.map.boxZoom.isEnabled()) {
                window.map.boxZoom.enable();
            }
            if (!window.map.dragRotate.isEnabled()) {
                window.map.dragRotate.enable();
            }
            if (!window.map.keyboard.isEnabled()) {
                window.map.keyboard.enable();
            }
            if (!window.map.doubleClickZoom.isEnabled()) {
                window.map.doubleClickZoom.enable();
            }
            if (!window.map.touchZoomRotate.isEnabled()) {
                window.map.touchZoomRotate.enable();
            }

            // Ensure container styles allow interactions
            const mapContainer = document.getElementById('projectMap');
            const mapCanvas = window.map.getCanvas();

            if (mapContainer) {
                mapContainer.style.pointerEvents = 'auto !important';
                mapContainer.style.touchAction = 'manipulation';
                mapContainer.style.cursor = 'grab';
            }

            if (mapCanvas) {
                mapCanvas.style.pointerEvents = 'auto !important';
                mapCanvas.style.touchAction = 'manipulation';
                mapCanvas.style.cursor = 'grab';
            }

            // Update markers with current project data using smart system
            if (window.filterMapByStatus && typeof window.filterMapByStatus === 'function') {
                console.log('🗺️ Using template map system for Mapbox auto-refresh marker update');
                // Template map handles its own markers, don't interfere
            } else if (typeof window.loadProjectMarkers === 'function') {
                console.log('🗺️ Using dashboard-complete.js smart marker system for Mapbox auto-refresh');
                window.loadProjectMarkers();
            } else {
                // Fallback: add markers directly
                this.addMapboxMarkers(projects);
            }

            console.log('✅ Mapbox map updated with interactions enabled');
        } catch (error) {
            console.warn('Failed to update Mapbox map:', error);
        }
    }

    clearAllMapMarkers() {
        // Clear Leaflet markers
        if (window.projectMap && window.markersLayer) {
            window.markersLayer.clearLayers();
        }

        // Clear Mapbox markers
        if (window.map && window.map.getSource && window.map.getSource('projects')) {
            window.map.getSource('projects').setData({
                type: 'FeatureCollection',
                features: []
            });
        }
    }

    addLeafletMarkers(projects) {
        if (!window.L || !window.projectMap || !window.markersLayer) return;

        projects.forEach(project => {
            if (project.gps_coordinates) {
                try {
                    const [lat, lng] = project.gps_coordinates.split(',').map(coord => parseFloat(coord.trim()));
                    if (!isNaN(lat) && !isNaN(lng)) {
                        const marker = window.L.marker([lat, lng])
                            .bindPopup(`<strong>${project.project_name}</strong><br>${project.location || ''}`);
                        window.markersLayer.addLayer(marker);
                    }
                } catch (error) {
                    console.warn(`Failed to add marker for project ${project.id}:`, error);
                }
            }
        });
    }

    addMapboxMarkers(projects) {
        if (!window.map || !window.map.getSource) return;

        const features = projects
            .filter(project => project.gps_coordinates)
            .map(project => {
                try {
                    const [lng, lat] = project.gps_coordinates.split(',').map(coord => parseFloat(coord.trim()));
                    if (!isNaN(lat) && !isNaN(lng)) {
                        return {
                            type: 'Feature',
                            geometry: {
                                type: 'Point',
                                coordinates: [lng, lat]
                            },
                            properties: {
                                title: project.project_name,
                                description: project.location || ''
                            }
                        };
                    }
                } catch (error) {
                    console.warn(`Failed to process project ${project.id} for Mapbox:`, error);
                }
                return null;
            })
            .filter(feature => feature !== null);

        if (window.map.getSource('projects')) {
            window.map.getSource('projects').setData({
                type: 'FeatureCollection',
                features: features
            });
        }
    }

    showMinimalistNotification(message, type = 'info') {
        // Remove existing notifications
        document.querySelectorAll('.minimalist-update-notification').forEach(el => el.remove());

        const notification = document.createElement('div');
        notification.className = 'minimalist-update-notification fixed top-4 left-1/2 transform -translate-x-1/2 px-3 py-1 rounded-full text-xs shadow-lg z-50 transition-all duration-300';

        if (type === 'success') {
            notification.className += ' bg-green-100 text-green-800 border border-green-200';
            notification.innerHTML = `<span class="font-medium">✓ ${message}</span>`;
        } else if (type === 'error') {
            notification.className += ' bg-red-100 text-red-800 border border-red-200';
            notification.innerHTML = `<span class="font-medium">✕ ${message}</span>`;
        } else {
            notification.className += ' bg-blue-100 text-blue-800 border border-blue-200';
            notification.innerHTML = `<span class="font-medium">${message}</span>`;
        }

        notification.style.opacity = '0';
        notification.style.transform = 'translateX(-50%) translateY(-10px)';

        document.body.appendChild(notification);

        requestAnimationFrame(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(-50%) translateY(0)';
        });

        // Auto-hide timing based on type
        const hideDelay = type === 'success' ? 1500 : type === 'error' ? 3000 : 2000;
        setTimeout(() => {
            this.hideMinimalistNotification();
        }, hideDelay);
    }

    hideMinimalistNotification() {
        const notifications = document.querySelectorAll('.minimalist-update-notification');
        notifications.forEach(notification => {
            if (notification.parentNode) {
                notification.style.opacity = '0';
                notification.style.transform = 'translateX(-50%) translateY(-10px)';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 300);
            }
        });
    }

    handleError(error) {
        this.retryCount++;

        if (this.retryCount >= this.maxRetries) {
            this.showMinimalistNotification('Update failed', 'error');
            this.showConnectionStatus('Update failed');

            // Increase interval on failure
            this.refreshInterval = Math.min(this.refreshInterval * 1.5, 120000);
            this.startAutoRefresh();
        } else {
            // Show retry notification
            this.showMinimalistNotification(`Retrying... (${this.retryCount}/${this.maxRetries})`);
            setTimeout(() => this.fetchAndUpdate(), 5000);
        }
    }

    showNotification(type, message) {
        const existing = document.querySelectorAll('.auto-refresh-notification');
        existing.forEach(el => el.remove());

        const notification = document.createElement('div');
        notification.className = 'auto-refresh-notification fixed top-6 left-1/2 transform -translate-x-1/2 px-6 py-4 rounded-xl text-white text-sm shadow-2xl z-50 transition-all duration-500 border border-white/20 backdrop-blur-xl';

        const colors = {
            success: 'bg-gradient-to-br from-emerald-500 via-green-500 to-teal-600',
            error: 'bg-gradient-to-br from-red-500 via-red-600 to-red-700',
            info: 'bg-gradient-to-br from-indigo-600 via-blue-600 to-purple-700'
        };

        const icons = {
            success: `<svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                      </svg>`,
            error: `<svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
                    </svg>`,
            info: `<div class="w-4 h-4 border-2 border-white/70 border-t-transparent rounded-full animate-spin"></div>`
        };

        notification.className += ` ${colors[type] || colors.info}`;
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(-50%) translateY(-20px) scale(0.9)';

        notification.innerHTML = `
            <div class="relative flex items-center space-x-3">
                <div class="flex-shrink-0">
                    ${icons[type] || icons.info}
                </div>
                <div class="flex flex-col">
                    <span class="font-bold text-base bg-gradient-to-r from-white to-blue-100 bg-clip-text text-transparent">
                        ${type === 'success' ? 'Dashboard Updated' : type === 'error' ? 'Update Failed' : 'Updating Dashboard'}
                    </span>
                    <span class="text-sm text-white/90 font-medium">${message}</span>
                </div>
                ${type === 'info' ? `
                    <div class="flex space-x-1">
                        <div class="w-2 h-2 bg-white/80 rounded-full animate-bounce"></div>
                        <div class="w-2 h-2 bg-white/80 rounded-full animate-bounce" style="animation-delay: 200ms"></div>
                        <div class="w-2 h-2 bg-white/80 rounded-full animate-bounce" style="animation-delay: 400ms"></div>
                    </div>
                ` : ''}
            </div>
            <div class="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-white/30 to-transparent ${type === 'info' ? 'animate-pulse' : ''}"></div>
        `;

        document.body.appendChild(notification);

        requestAnimationFrame(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(-50%) translateY(0) scale(1)';
        });

        if (type !== 'info') {
            setTimeout(() => {
                notification.style.opacity = '0';
                notification.style.transform = 'translateX(-50%) translateY(-20px) scale(0.9)';
                setTimeout(() => notification.remove(), 500);
            }, type === 'error' ? 5000 : 3000);
        }
    }

    showConnectionStatus(status) {
        let statusEl = document.getElementById('autoRefreshStatus');
        if (!statusEl) {
            statusEl = document.createElement('div');
            statusEl.id = 'autoRefreshStatus';
            statusEl.className = 'fixed bottom-6 left-6 px-4 py-3 rounded-xl text-sm shadow-2xl z-40 transition-all duration-500 border border-white/30 backdrop-blur-lg';
            document.body.appendChild(statusEl);
        }

        const statusConfig = {
            'active': {
                class: 'bg-gradient-to-r from-emerald-500/90 to-green-500/90 text-white border-green-400/50',
                icon: `<svg class="w-4 h-4 text-green-200" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                      </svg>`,
                pulse: false
            },
            'online': {
                class: 'bg-gradient-to-r from-emerald-500/90 to-green-500/90 text-white border-green-400/50',
                icon: `<svg class="w-4 h-4 text-green-200" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                      </svg>`,
                pulse: false
            },
            'failed': {
                class: 'bg-gradient-to-r from-red-500/90 to-red-700/90 text-white border-red-400/50',
                icon: `<svg class="w-4 h-4 text-red-200" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
                      </svg>`,
                pulse: true
            },
            'offline': {
                class: 'bg-gradient-to-r from-red-500/90 to-red-600/90 text-white border-red-400/50',
                icon: `<svg class="w-4 h-4 text-red-200" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                      </svg>`,
                pulse: true
            }
        };

        // Find matching config by checking if status contains the key
        let config = null;
        for (const [key, value] of Object.entries(statusConfig)) {
            if (status.toLowerCase().includes(key)) {
                config = value;
                break;
            }
        }

        // Default to blue for unknown statuses
        if (!config) {
            config = {
                class: 'bg-gradient-to-r from-blue-500/90 to-indigo-500/90 text-white border-blue-400/50',
                icon: `<div class="w-4 h-4 border-2 border-blue-200 border-t-transparent rounded-full animate-spin"></div>`,
                pulse: false
            };
        }

        statusEl.className = `fixed bottom-6 left-6 px-4 py-3 rounded-xl text-sm shadow-2xl z-40 transition-all duration-500 border backdrop-blur-lg ${config.class} ${config.pulse ? 'animate-pulse' : ''}`;
        statusEl.innerHTML = `
            <div class="flex items-center space-x-2">
                <div class="flex-shrink-0">${config.icon}</div>
                <span class="font-medium">${status}</span>
                <div class="text-xs opacity-75">${new Date().toLocaleTimeString()}</div>
            </div>
        `;

        // Auto-hide successful connection status after 3 seconds
        if (status.includes('active') || status.includes('online')) {
            setTimeout(() => {
                if (statusEl && (statusEl.textContent.includes('active') || statusEl.textContent.includes('online'))) {
                    statusEl.style.opacity = '0';
                    statusEl.style.transform = 'translateY(10px)';
                    setTimeout(() => statusEl.remove(), 500);
                }
            }, 3000);
        }
    }

    addEventListeners() {
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.isActive) {
                this.fetchAndUpdate();
            }
        });

        window.addEventListener('online', () => {
            this.showConnectionStatus('Back online');
            this.fetchAndUpdate();
        });

        window.addEventListener('offline', () => {
            this.showConnectionStatus('Offline');
        });
    }

    pause() {
        this.isActive = false;
        this.showConnectionStatus('Paused');
    }

    resume() {
        this.isActive = true;
        this.showConnectionStatus('Resumed');
        this.fetchAndUpdate();
    }

    destroy() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
        this.isActive = false;
        
        const statusEl = document.getElementById('autoRefreshStatus');
        if (statusEl) statusEl.remove();
    }
}
// ====================================================================
// INTERACTIONS & EVENT HANDLERS
// ====================================================================

function initializeInteractions() {
    initializeStatusCardFilters();
    initializeSearchFeatures();
    initializeKeyboardShortcuts();
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
            } else {
                activeFilter = status;
                
                filterCards.forEach(c => {
                    c.classList.remove('ring-4', 'ring-blue-300', 'ring-opacity-50');
                    c.style.transform = 'scale(1)';
                });
                
                this.classList.add('ring-4', 'ring-blue-300', 'ring-opacity-50');
                this.style.transform = 'scale(1.02)';
                this.style.transition = 'all 0.3s ease';
                
                filterProjectsByStatus(status);
            }
            
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = activeFilter === status ? 'scale(1.02)' : 'scale(1)';
            }, 150);
        });
        
        card.addEventListener('mouseenter', function() {
            if (activeFilter !== this.dataset.status) {
                this.style.transform = 'scale(1.02)';
            }
        });
        
        card.addEventListener('mouseleave', function() {
            if (activeFilter !== this.dataset.status) {
                this.style.transform = 'scale(1)';
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
    showFilterIndicator(status, filteredProjects.length);
}

function showAllProjects() {
    if (!window.dashboardData?.projects) return;
    
    updateChartsWithFilteredData(window.dashboardData.projects);
    updateCalendarWithFilteredData(window.dashboardData.projects);
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

    // Update map markers with filtered projects
    updateMapMarkersWithFilteredData(projects);
}

function updateCalendarWithFilteredData(projects) {
    if (!window.dashboardCalendar) return;

    const projectColors = generateProjectColors(projects);
    const events = generateCalendarEvents(projects, projectColors);

    window.dashboardCalendar.removeAllEvents();
    window.dashboardCalendar.addEventSource(events);
}

function updateMapMarkersWithFilteredData(projects) {
    console.log('🗺️ Updating map markers with filtered data:', projects.length, 'projects');

    // Check if template map system is available and use it
    if (window.filterMapByStatus && typeof window.filterMapByStatus === 'function') {
        console.log('✅ Using template map filtering system');

        // If we have filtered projects, determine the common status to filter by
        if (projects.length > 0 && projects.length < window.dashboardData?.projects?.length) {
            // Find the common status among filtered projects
            const statuses = [...new Set(projects.map(p => p.status))];
            if (statuses.length === 1) {
                // All projects have the same status, filter by it
                window.filterMapByStatus(statuses[0]);
                console.log(`✅ Template map filtered by status: ${statuses[0]}`);
                return;
            }
        }

        // If no specific status or showing all projects, clear filters
        window.filterMapByStatus(null);
        console.log('✅ Template map filter cleared - showing all projects');
        return;
    }

    // Fallback to dashboard-complete.js map system with smart marker updates
    console.log('⚠️ Template map not available, using smart marker update system');

    // Get the map reference
    const map = projectMap || window.projectMap || window.map;
    if (!map) {
        console.warn('❌ No map found to update markers');
        return;
    }

    // Use smart marker update instead of clearing all
    smartUpdateMapMarkers(projects, map);
}

// Smart marker update system to prevent duplication and unnecessary updates
function smartUpdateMapMarkers(projects, map) {
    console.log('🔄 Smart updating map markers...');

    // Initialize marker tracking if not exists
    if (!window.markerTracker) {
        window.markerTracker = {
            markers: new Map(), // projectId -> marker object
            lastUpdate: new Map(), // projectId -> hash of project data
            visibleProjects: new Set() // currently visible project IDs
        };
    }

    const tracker = window.markerTracker;
    const newVisibleProjects = new Set();
    let markersAdded = 0;
    let markersUpdated = 0;
    let markersRemoved = 0;
    let markersSkipped = 0;

    // Helper function to create a hash of project data for change detection
    function getProjectHash(project) {
        return JSON.stringify({
            id: project.id || project.project_id,
            name: project.name || project.project_name,
            status: project.status,
            gps_coordinates: project.gps_coordinates,
            location: project.location,
            progress: project.progress || project.actual_progress
        });
    }

    // Process each project in the filtered list
    projects.forEach(project => {
        const projectId = project.id || project.project_id || project.name || project.project_name;
        if (!projectId) {
            markersSkipped++;
            return;
        }

        newVisibleProjects.add(projectId);

        if (!project.gps_coordinates) {
            markersSkipped++;
            return;
        }

        try {
            const [lat, lng] = project.gps_coordinates.split(',').map(coord => parseFloat(coord.trim()));

            if (isNaN(lat) || isNaN(lng)) {
                markersSkipped++;
                return;
            }

            const currentHash = getProjectHash(project);
            const existingMarker = tracker.markers.get(projectId);
            const lastHash = tracker.lastUpdate.get(projectId);

            // Check if marker needs to be created or updated
            if (!existingMarker) {
                // Create new marker
                console.log(`➕ Creating new marker for project: ${project.name || projectId}`);
                const newMarker = createSmartProjectMarker(project, lat, lng, map);
                if (newMarker) {
                    tracker.markers.set(projectId, newMarker);
                    tracker.lastUpdate.set(projectId, currentHash);
                    markersAdded++;
                }
            } else if (lastHash !== currentHash) {
                // Update existing marker
                console.log(`🔄 Updating marker for project: ${project.name || projectId}`);
                updateExistingMarker(existingMarker, project, lat, lng);
                tracker.lastUpdate.set(projectId, currentHash);
                markersUpdated++;
            } else {
                // Marker exists and is up to date, ensure it's visible
                if (!map.hasLayer(existingMarker)) {
                    map.addLayer(existingMarker);
                    console.log(`👁️ Showing existing marker: ${project.name || projectId}`);
                }
            }

        } catch (error) {
            console.warn('Failed to parse coordinates for project:', project.name, error);
            markersSkipped++;
        }
    });

    // Remove markers for projects that are no longer visible
    tracker.visibleProjects.forEach(projectId => {
        if (!newVisibleProjects.has(projectId)) {
            const marker = tracker.markers.get(projectId);
            if (marker && map.hasLayer(marker)) {
                map.removeLayer(marker);
                markersRemoved++;
                console.log(`👁️‍🗨️ Hiding marker for filtered project: ${projectId}`);
            }
        }
    });

    // Update visible projects set
    tracker.visibleProjects = newVisibleProjects;

    console.log(`✅ Smart marker update complete: ${markersAdded} added, ${markersUpdated} updated, ${markersRemoved} hidden, ${markersSkipped} skipped`);

    // Update map statistics
    const activeProjects = projects.filter(p => p.status === 'OG' || p.status === 'IP').length;
    updateMapStats(projects.length, newVisibleProjects.size, activeProjects);
}

// Create a new marker with smart tracking
function createSmartProjectMarker(project, lat, lng, map) {
    try {
        const status = project.status || 'PL';
        const color = statusColors[status] || statusColors['PL'];

        // Create custom icon based on project status
        const markerIcon = L.divIcon({
            className: 'custom-project-marker smart-marker',
            html: `
                <div style="
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
                ">
                    ${getStatusIcon(status)}
                </div>
            `,
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        });

        // Create marker
        const marker = L.marker([lat, lng], { icon: markerIcon });

        // Store project data with marker for future updates
        marker.projectData = project;
        marker.projectId = project.id || project.project_id || project.name || project.project_name;

        // Add click event to show project details
        marker.on('click', function(e) {
            showProjectPopup(project, e.latlng);
        });

        // Add hover effect
        marker.on('mouseover', function() {
            this.getElement().style.transform = 'scale(1.2)';
            this.getElement().style.zIndex = '1000';
        });

        marker.on('mouseout', function() {
            this.getElement().style.transform = 'scale(1)';
            this.getElement().style.zIndex = '600';
        });

        // Add to map
        marker.addTo(map);

        return marker;
    } catch (error) {
        console.error('Failed to create smart marker:', error);
        return null;
    }
}

// Update an existing marker with new data
function updateExistingMarker(marker, project, lat, lng) {
    try {
        // Update position if coordinates changed
        const currentLatLng = marker.getLatLng();
        if (Math.abs(currentLatLng.lat - lat) > 0.001 || Math.abs(currentLatLng.lng - lng) > 0.001) {
            marker.setLatLng([lat, lng]);
            console.log(`📍 Updated position for marker: ${project.name}`);
        }

        // Update icon if status changed
        const currentStatus = marker.projectData?.status;
        const newStatus = project.status || 'PL';

        if (currentStatus !== newStatus) {
            const color = statusColors[newStatus] || statusColors['PL'];
            const newIcon = L.divIcon({
                className: 'custom-project-marker smart-marker',
                html: `
                    <div style="
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
                    ">
                        ${getStatusIcon(newStatus)}
                    </div>
                `,
                iconSize: [24, 24],
                iconAnchor: [12, 12]
            });
            marker.setIcon(newIcon);
            console.log(`🎨 Updated icon for marker: ${project.name} (${currentStatus} → ${newStatus})`);
        }

        // Update stored project data
        marker.projectData = project;

        // Update click handler with new data
        marker.off('click');
        marker.on('click', function(e) {
            showProjectPopup(project, e.latlng);
        });

    } catch (error) {
        console.error('Failed to update existing marker:', error);
    }
}

// Clear all marker tracking (useful for full refreshes)
function clearMarkerTracking() {
    if (window.markerTracker) {
        // Remove all tracked markers from map
        const map = projectMap || window.projectMap || window.map;
        if (map) {
            window.markerTracker.markers.forEach(marker => {
                if (map.hasLayer(marker)) {
                    map.removeLayer(marker);
                }
            });
        }

        // Clear tracking data
        window.markerTracker.markers.clear();
        window.markerTracker.lastUpdate.clear();
        window.markerTracker.visibleProjects.clear();

        console.log('🧹 Cleared all marker tracking data');
    }
}

// Expose smart marker functions globally
window.smartUpdateMapMarkers = smartUpdateMapMarkers;
window.clearMarkerTracking = clearMarkerTracking;

// Force hide map loading overlay and enable interactions
function forceEnableMapInteractions() {
    console.log('🔧 Force enabling map interactions...');

    // Hide loading overlay immediately
    const loadingEl = document.getElementById('mapLoading');
    if (loadingEl) {
        loadingEl.style.display = 'none';
        loadingEl.style.visibility = 'hidden';
        loadingEl.style.pointerEvents = 'none';
        console.log('✅ Map loading overlay hidden');
    }

    // Ensure map container has proper CSS
    const mapContainer = document.getElementById('projectMap');
    if (mapContainer) {
        mapContainer.style.pointerEvents = 'auto';
        mapContainer.style.touchAction = 'manipulation';
        mapContainer.style.userSelect = 'none';
        mapContainer.style.cursor = 'grab';
        console.log('✅ Map container interaction CSS applied');

        // Also apply to all child elements
        const allChildren = mapContainer.querySelectorAll('*');
        allChildren.forEach(child => {
            child.style.pointerEvents = 'auto';
            child.style.touchAction = 'manipulation';
        });
        console.log('✅ Map children interaction CSS applied');
    }

    // Check if Leaflet map exists and enable interactions
    const map = projectMap || window.projectMap || window.map;
    if (map && map.dragging) {
        map.dragging.enable();
        map.scrollWheelZoom.enable();
        map.doubleClickZoom.enable();
        map.boxZoom.enable();
        map.keyboard.enable();
        console.log('✅ Leaflet map interactions enabled');

        // Test map interaction capabilities
        console.log('🧪 Map interaction test:', {
            dragging: map.dragging.enabled(),
            scrollWheelZoom: map.scrollWheelZoom.enabled(),
            doubleClickZoom: map.doubleClickZoom.enabled(),
            boxZoom: map.boxZoom.enabled(),
            keyboard: map.keyboard.enabled()
        });
    }

    console.log('🎯 Map interaction setup complete');
}

// Expose globally for testing
window.forceEnableMapInteractions = forceEnableMapInteractions;

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
}

function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        
        switch (e.key) {
            case '1':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    document.querySelector('[data-status="PL"]')?.click();
                }
                break;
            case '2':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    document.querySelector('[data-status="OG"]')?.click();
                }
                break;
            case '3':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    document.querySelector('[data-status="CP"]')?.click();
                }
                break;
            case '4':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    document.querySelector('[data-status="CN"]')?.click();
                }
                break;
            case 'r':
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    if (window.dashboardAutoRefresh) {
                        window.dashboardAutoRefresh.fetchAndUpdate();
                    }
                }
                break;
            case 'Escape':
                // Close any open modals or filters
                closeTaskModal();
                showAllProjects();
                break;
        }
    });
}

// ====================================================================
// ADDITIONAL UTILITY FUNCTIONS
// ====================================================================

function refreshDashboard() {
    if (window.dashboardAutoRefresh) {
        window.dashboardAutoRefresh.fetchAndUpdate();
    }
}

function toggleAutoRefresh() {
    if (window.dashboardAutoRefresh) {
        if (window.dashboardAutoRefresh.isActive) {
            window.dashboardAutoRefresh.pause();
            showInfoMessage('Auto-refresh paused');
        } else {
            window.dashboardAutoRefresh.resume();
            showInfoMessage('Auto-refresh resumed');
        }
    }
}

function exportDashboardData() {
    if (!window.dashboardData) {
        showErrorMessage('No data available to export');
        return;
    }
    
    const data = {
        exported_at: new Date().toISOString(),
        projects: window.dashboardData.projects,
        metrics: window.dashboardData.metrics,
        status_counts: window.dashboardData.status_counts,
        task_status_counts: window.dashboardData.task_status_counts
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `dashboard-data-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showSuccessMessage('Dashboard data exported successfully');
}

function printDashboard() {
    // Hide interactive elements before printing
    const elementsToHide = document.querySelectorAll('.no-print, button, .auto-refresh-notification');
    elementsToHide.forEach(el => el.style.display = 'none');
    
    window.print();
    
    // Restore elements after printing
    setTimeout(() => {
        elementsToHide.forEach(el => el.style.display = '');
    }, 1000);
}

// ====================================================================
// PERFORMANCE MONITORING
// ====================================================================

function monitorPerformance() {
    // Monitor chart render times
    const originalRender = Chart.prototype.render;
    Chart.prototype.render = function() {
        const start = performance.now();
        const result = originalRender.apply(this, arguments);
        const end = performance.now();
        console.log(`Chart render took ${(end - start).toFixed(2)}ms`);
        return result;
    };
    
    // Monitor calendar render times
    if (window.FullCalendar) {
        const originalCalendarRender = FullCalendar.Calendar.prototype.render;
        FullCalendar.Calendar.prototype.render = function() {
            const start = performance.now();
            const result = originalCalendarRender.apply(this, arguments);
            const end = performance.now();
            console.log(`Calendar render took ${(end - start).toFixed(2)}ms`);
            return result;
        };
    }
}

// Initialize performance monitoring in development
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    monitorPerformance();
}

// ====================================================================
// GLOBAL EXPORTS & CLEANUP
// ====================================================================

// Global functions for template use
window.closeTaskModal = closeTaskModal;
window.showAllProjects = showAllProjects;
window.filterProjectsByStatus = filterProjectsByStatus;
window.refreshDashboard = refreshDashboard;
window.toggleAutoRefresh = toggleAutoRefresh;
window.exportDashboardData = exportDashboardData;
window.printDashboard = printDashboard;

// Utility exports
window.dashboardUtils = {
    showAllProjects,
    filterProjectsByStatus,
    showSuccessMessage,
    showErrorMessage,
    showInfoMessage,
    closeTaskModal,
    refreshDashboard,
    toggleAutoRefresh,
    exportDashboardData,
    printDashboard
};

// Control methods for debugging and testing
window.refreshControls = {
    pause: () => window.dashboardAutoRefresh?.pause(),
    resume: () => window.dashboardAutoRefresh?.resume(),
    refresh: () => window.dashboardAutoRefresh?.fetchAndUpdate(),
    setInterval: (seconds) => {
        if (window.dashboardAutoRefresh) {
            window.dashboardAutoRefresh.refreshInterval = seconds * 1000;
            window.dashboardAutoRefresh.startAutoRefresh();
        }
    },
    status: () => console.log({
        isActive: window.dashboardAutoRefresh?.isActive,
        interval: window.dashboardAutoRefresh?.refreshInterval,
        lastUpdate: window.dashboardAutoRefresh?.lastUpdateTimestamp,
        retryCount: window.dashboardAutoRefresh?.retryCount
    })
};

// Debug helpers
window.debugDashboard = {
    logData: () => console.log('Dashboard Data:', window.dashboardData),
    logCharts: () => console.log('Charts:', { progress: window.progressChart, budget: window.budgetChart }),
    logCalendar: () => console.log('Calendar:', window.dashboardCalendar),
    logAutoRefresh: () => console.log('Auto-refresh:', window.dashboardAutoRefresh),
    logMap: () => console.log('Map:', {
        map: projectMap,
        markers: projectMarkers,
        container: document.getElementById('projectMap'),
        leafletLoaded: typeof L !== 'undefined'
    }),
    simulateError: () => window.dashboardAutoRefresh?.handleError(new Error('Simulated error')),
    clearCache: () => {
        window.dashboardData = null;
        clearMarkerTracking();
        showInfoMessage('Dashboard cache and marker tracking cleared');
    },
    reinitializeMap: () => {
        console.log('Manually reinitializing map...');
        initializeprojectMap();
    },
    inspectMarkerTracking: () => {
        if (window.markerTracker) {
            console.log('📊 Marker Tracking Status:', {
                totalMarkers: window.markerTracker.markers.size,
                visibleProjects: window.markerTracker.visibleProjects.size,
                trackedProjects: Array.from(window.markerTracker.markers.keys()),
                visibleProjects: Array.from(window.markerTracker.visibleProjects),
                markersOnMap: Array.from(window.markerTracker.markers.values()).filter(marker => {
                    const map = projectMap || window.projectMap || window.map;
                    return map && map.hasLayer(marker);
                }).length
            });
        } else {
            console.log('❌ No marker tracking initialized');
        }
    },
    fixMapInteractions: () => {
        console.log('🔧 Attempting to fix map interactions...');
        forceEnableMapInteractions();
    },
    testMapInteractivity: () => {
        const mapContainer = document.getElementById('projectMap');
        const loadingOverlay = document.getElementById('mapLoading');
        const map = projectMap || window.projectMap || window.map;

        console.log('🔍 Map Interactivity Diagnosis:', {
            mapContainer: {
                exists: !!mapContainer,
                pointerEvents: mapContainer?.style.pointerEvents || 'default',
                touchAction: mapContainer?.style.touchAction || 'default',
                cursor: mapContainer?.style.cursor || 'default',
                zIndex: mapContainer?.style.zIndex || 'auto'
            },
            loadingOverlay: {
                exists: !!loadingOverlay,
                display: loadingOverlay?.style.display || 'block',
                visibility: loadingOverlay?.style.visibility || 'visible',
                pointerEvents: loadingOverlay?.style.pointerEvents || 'auto',
                zIndex: loadingOverlay?.style.zIndex || 'auto'
            },
            leafletMap: {
                exists: !!map,
                dragging: map?.dragging?.enabled(),
                scrollWheelZoom: map?.scrollWheelZoom?.enabled(),
                doubleClickZoom: map?.doubleClickZoom?.enabled(),
                boxZoom: map?.boxZoom?.enabled(),
                keyboard: map?.keyboard?.enabled()
            }
        });
    },
    testMapContainer: () => {
        const container = document.getElementById('projectMap');
        console.log('Map container test:', {
            exists: !!container,
            dimensions: container ? {
                width: container.offsetWidth,
                height: container.offsetHeight,
                clientWidth: container.clientWidth,
                clientHeight: container.clientHeight,
                scrollWidth: container.scrollWidth,
                scrollHeight: container.scrollHeight
            } : null,
            style: container ? container.style.cssText : null,
            computedStyle: container ? {
                height: window.getComputedStyle(container).height,
                width: window.getComputedStyle(container).width,
                display: window.getComputedStyle(container).display,
                position: window.getComputedStyle(container).position
            } : null,
            leafletContainer: container ? container.querySelector('.leaflet-container') : null
        });

        if (projectMap) {
            console.log('Leaflet map state:', {
                center: projectMap.getCenter(),
                zoom: projectMap.getZoom(),
                bounds: projectMap.getBounds(),
                size: projectMap.getSize(),
                containerPoint: projectMap.getContainer()
            });
        }
    },
    fixMapViewport: () => {
        console.log('Attempting to fix map viewport...');
        if (projectMap) {
            const container = document.getElementById('projectMap');
            if (container) {
                // Force container dimensions to new height
                container.style.height = '320px';
                container.style.width = '100%';
                container.style.display = 'block';

                // Invalidate size and reset view
                projectMap.invalidateSize(true);
                setTimeout(() => {
                    projectMap.fitBounds(philippinesBounds, {
                        padding: [20, 20],
                        maxZoom: 8
                    });
                    projectMap.invalidateSize(true);
                }, 100);

                console.log('Map viewport fix attempted with new dimensions');
            }
        }
    }
};

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.dashboardAutoRefresh) {
        window.dashboardAutoRefresh.destroy();
    }
    
    // Clean up any remaining intervals or timeouts
    if (window.progressChart) {
        window.progressChart.destroy();
    }
    if (window.budgetChart) {
        window.budgetChart.destroy();
    }
    if (window.dashboardCalendar) {
        window.dashboardCalendar.destroy();
    }
    
    console.log('Dashboard cleanup completed');
});

// Add CSS for print styles
const printStyles = `
    <style media="print">
        .no-print { display: none !important; }
        .filter-card { box-shadow: none !important; transform: none !important; }
        .auto-refresh-notification { display: none !important; }
        #autoRefreshStatus { display: none !important; }
        button { display: none !important; }
        .fixed { position: relative !important; }
        @page { margin: 1in; }
        body { font-size: 12px; }
        .text-3xl { font-size: 1.5rem !important; }
        .text-2xl { font-size: 1.25rem !important; }
        .text-xl { font-size: 1.125rem !important; }
    </style>
`;

document.head.insertAdjacentHTML('beforeend', printStyles);


// ====================================================================
// PROJECT LOCATIONS MAP
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
const statusColors = {
    'PL': '#3b82f6', // blue - Planned
    'IP': '#f97316', // orange - In Progress
    'CP': '#22c55e', // green - Completed
    'CN': '#ef4444'  // red - Cancelled
};

function initializeprojectMap() {
    console.log('🗺️ Starting initializeprojectMap function...');

    const mapContainer = document.getElementById('projectMap');
    if (!mapContainer) {
        console.error('❌ Map container #projectMap not found in DOM');
        return;
    }

    console.log('✅ Map container found:', mapContainer);

    // Check if Leaflet is loaded
    if (typeof L === 'undefined') {
        console.error('❌ Leaflet library not loaded. Retrying in 1 second...');
        setTimeout(initializeprojectMap, 1000);
        return;
    }

    console.log('✅ Leaflet library loaded, version:', L.version);

    try {
        console.log('🔧 Starting map initialization process...');
        // Remove existing map if it exists
        if (projectMap) {
            projectMap.remove();
            projectMap = null;
        }

        // Ensure container has proper dimensions and clear any existing content
        mapContainer.innerHTML = '';
        mapContainer.style.height = '400px';
        mapContainer.style.width = '100%';
        mapContainer.style.position = 'relative';
        mapContainer.style.zIndex = '1';


        console.log('🗺️ About to create Leaflet map with config...');

        // Initialize enhanced Leaflet map with better configuration
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
            preferCanvas: true, // Better performance
            fadeAnimation: true,
            zoomAnimation: true,
            markerZoomAnimation: true
        });

        console.log('✅ Leaflet map object created successfully!');

        console.log('Map object created:', projectMap);

        // Expose map globally for access from other functions
        window.projectMap = projectMap;
        window.projectMap = projectMap;  // For compatibility
        console.log('Map exposed globally as window.projectMap and window.projectMap');

        // Add OpenStreetMap tiles with error handling
        const tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19,
            errorTileUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
        });

        tileLayer.on('loading', () => console.log('Tiles loading...'));
        tileLayer.on('load', () => console.log('Tiles loaded'));
        tileLayer.on('tileerror', (e) => console.warn('Tile error:', e));

        tileLayer.addTo(projectMap);
        console.log('Tile layer added');

        // Add interaction event listeners for debugging
        projectMap.on('movestart', () => console.log('🖱️ Map move started'));
        projectMap.on('move', () => console.log('🖱️ Map moving'));
        projectMap.on('moveend', () => console.log('✅ Map move ended'));
        projectMap.on('zoomstart', () => console.log('🔍 Map zoom started'));
        projectMap.on('zoom', () => console.log('🔍 Map zooming'));
        projectMap.on('zoomend', () => console.log('✅ Map zoom ended'));
        projectMap.on('click', (e) => console.log('👆 Map clicked at:', e.latlng));

        console.log('🎯 Map interaction events added for debugging');

        // Hide loading placeholder
        const loadingPlaceholder = document.getElementById('mapLoadingPlaceholder');
        if (loadingPlaceholder) {
            loadingPlaceholder.style.display = 'none';
        }

        // Enhanced map initialization sequence
        setTimeout(() => {
            if (projectMap) {
                console.log('Starting enhanced map initialization...');

                // Step 1: Force initial size calculation
                projectMap.invalidateSize(true);

                // Step 2: Set initial view to Philippines
                projectMap.setView(philippinesCenter, 6);

                // Step 3: Multiple resize attempts with progressive delays
                [100, 250, 500].forEach((delay, index) => {
                    setTimeout(() => {
                        projectMap.invalidateSize(true);
                        console.log(`Map resize attempt ${index + 1} completed`);

                        // On final resize, fit bounds and load markers
                        if (index === 2) {
                            projectMap.fitBounds(philippinesBounds, {
                                padding: [20, 20],
                                maxZoom: 8,
                                animate: true,
                                duration: 1
                            });

                            // Load markers after everything is set up
                            setTimeout(() => {
                                loadProjectMarkers();
                                console.log('✅ Enhanced Leaflet map fully initialized with proper viewport');
                            }, 300);
                        }
                    }, delay);
                });
            }
        }, 300);

        // Resize observer disabled - using modal map instead

        console.log('Projects map initialized successfully');

    } catch (error) {
        console.error('Error initializing projects map:', error);
        // Show error message in the container
        mapContainer.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; height: 320px; background: #f3f4f6; border-radius: 12px;">
                <div style="text-align: center; color: #6b7280; padding: 20px;">
                    <div style="font-size: 48px; margin-bottom: 16px;">🗺️</div>
                    <p style="font-weight: 600; margin-bottom: 8px;">Map failed to load</p>
                    <p style="font-size: 12px; margin-bottom: 16px;">Error: ${error.message}</p>
                    <button onclick="window.initializeprojectMap()" style="padding: 8px 16px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px;">
                        Retry Loading Map
                    </button>
                </div>
            </div>
        `;
    }
}

// Expose map functions to global scope immediately
window.initializeprojectMap = initializeprojectMap;
console.log('Map initialization function exposed to global scope');

// Add test function for map interactions
window.testLeafletMapInteractions = function() {
    console.log('🧪 Testing Leaflet map interactions...');

    if (!projectMap && !window.projectMap) {
        console.error('❌ No map found to test');
        return;
    }

    const map = projectMap || window.projectMap;

    console.log('- Map object:', map);
    console.log('- Dragging enabled:', map.dragging.enabled());
    console.log('- ScrollWheelZoom enabled:', map.scrollWheelZoom.enabled());
    console.log('- DoubleClickZoom enabled:', map.doubleClickZoom.enabled());
    console.log('- BoxZoom enabled:', map.boxZoom.enabled());
    console.log('- Keyboard enabled:', map.keyboard.enabled());

    // Test programmatic movement
    console.log('🧪 Testing programmatic map movement...');
    const currentCenter = map.getCenter();
    const currentZoom = map.getZoom();

    // Small pan test
    map.panBy([50, 50]);
    setTimeout(() => {
        map.setView(currentCenter, currentZoom);
        console.log('✅ Programmatic movement test completed');
    }, 1000);
};

function loadProjectMarkers() {
    console.log('📍 loadProjectMarkers() called - routing to smart update system');

    // Check if template map system is available first
    if (window.filterMapByStatus && typeof window.filterMapByStatus === 'function') {
        console.log('✅ Template map system detected - deferring to template markers');
        // Let the template handle markers, don't interfere
        return;
    }

    // Check for map availability
    if (!projectMap) {
        if (window.projectMap) {
            console.log('📍 Found map in window.projectMap, using that instead');
            projectMap = window.projectMap;
        } else {
            console.warn('❌ No map found in global scope');
            return;
        }
    }

    // Get project data
    let projectsData = [];

    if (window.dashboardData?.projects) {
        projectsData = window.dashboardData.projects;
        console.log('📊 Using dashboard data for smart marker update');
    } else {
        // Fallback: JSON script tag
        const projectsDataScript = document.getElementById('projects-data');
        if (projectsDataScript && projectsDataScript.textContent.trim()) {
            try {
                projectsData = JSON.parse(projectsDataScript.textContent);
                console.log('📊 Using script tag data for smart marker update');
            } catch (error) {
                console.error('❌ Error parsing projects data from script tag:', error);
                return;
            }
        } else {
            console.warn('⚠️ No projects data found');
            return;
        }
    }

    if (!Array.isArray(projectsData) || projectsData.length === 0) {
        console.warn('⚠️ No project data available for smart marker update');
        return;
    }

    // Use smart update system instead of old marker clearing/adding approach
    console.log('🧠 Using smart marker update system for', projectsData.length, 'projects');

    // Get the map reference
    const map = projectMap || window.projectMap || window.map;
    if (!map) {
        console.warn('❌ No map found for smart marker update');
        return;
    }

    // Route to smart update system
    smartUpdateMapMarkers(projectsData, map);
}

// Add sample markers for testing when no real data is available
function addSampleMarkers() {
    console.log('Adding sample markers for demonstration...');

    const sampleProjects = [
        {
            project_name: "Manila Office Tower",
            status: "OG",
            location: "Manila, Philippines",
            client_name: "Sample Client 1",
            estimated_cost: 5000000,
            start_date: "2024-01-15"
        },
        {
            project_name: "Cebu Resort Development",
            status: "PL",
            location: "Cebu, Philippines",
            client_name: "Sample Client 2",
            estimated_cost: 8000000,
            start_date: "2024-03-01"
        },
        {
            project_name: "Davao Shopping Center",
            status: "CP",
            location: "Davao, Philippines",
            client_name: "Sample Client 3",
            estimated_cost: 12000000,
            start_date: "2023-08-01"
        },
        {
            project_name: "Baguio Mountain Resort",
            status: "PL",
            location: "Baguio, Philippines",
            client_name: "Sample Client 4",
            estimated_cost: 6000000,
            start_date: "2024-05-01"
        }
    ];

    // Philippines major cities coordinates
    const sampleCoordinates = [
        [14.5995, 120.9842], // Manila
        [10.3157, 123.8854], // Cebu
        [7.1907, 125.4553],  // Davao
        [16.4023, 120.5960]  // Baguio
    ];

    sampleProjects.forEach((project, index) => {
        const [lat, lng] = sampleCoordinates[index];
        addProjectMarker(project, lat, lng);
        console.log(`✓ Added sample marker: ${project.project_name} at ${lat}, ${lng}`);
    });

    console.log(`Added ${sampleProjects.length} sample markers to the map`);

    // Update map statistics
    updateMapStats(sampleProjects.length, sampleProjects.length, sampleProjects.filter(p => p.status === 'OG').length);
}

// Function to update map statistics in the sidebar
function updateMapStats(totalProjects, mappedProjects, activeProjects) {
    const totalEl = document.getElementById('totalProjectsCount');
    const mappedEl = document.getElementById('mappedProjectsCount');
    const activeEl = document.getElementById('activeProjectsCount');

    if (totalEl) totalEl.textContent = totalProjects;
    if (mappedEl) mappedEl.textContent = mappedProjects;
    if (activeEl) activeEl.textContent = activeProjects;
}

// Expose loadProjectMarkers to global scope
window.loadProjectMarkers = loadProjectMarkers;

function addProjectMarker(project, lat, lng) {
    const status = project.status || 'PL';
    const color = statusColors[status] || statusColors['PL'];

    // Create custom icon based on project status
    const markerIcon = L.divIcon({
        className: 'custom-project-marker',
        html: `
            <div style="
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
            ">
                ${getStatusIcon(status)}
            </div>
        `,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });

    // Create marker
    const marker = L.marker([lat, lng], { icon: markerIcon }).addTo(projectMap);

    // Add click event to show project details
    marker.on('click', function(e) {
        showProjectPopup(project, e.latlng);
    });

    // Add hover effect
    marker.on('mouseover', function() {
        this.getElement().style.transform = 'scale(1.2)';
        this.getElement().style.zIndex = '1000';
    });

    marker.on('mouseout', function() {
        this.getElement().style.transform = 'scale(1)';
        this.getElement().style.zIndex = '600';
    });

    projectMarkers.push(marker);

    // Keep global reference updated
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
        case 'IP': return 'In Progress';
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


// Global map control functions
window.centerMapOnPhilippines = function() {
    if (projectMap) {
        console.log('Centering map on Philippines...');
        // Force invalidate size first
        projectMap.invalidateSize(true);
        // Set view to Philippines with proper bounds
        projectMap.fitBounds(philippinesBounds, {
            padding: [20, 20],
            maxZoom: 8
        });
        // Fallback to center view
        setTimeout(() => {
            projectMap.setView(philippinesCenter, 6);
            projectMap.invalidateSize(true);
            console.log('Map centered and resized');
        }, 200);
    }
};


window.closeProjectPopup = closeProjectPopup;

// Map will be initialized as part of the main dashboard initialization
// No separate initialization needed here


console.log('Projects map functionality loaded!');

// Debug: Check if functions are available
console.log('Available map functions:', {
    initializeprojectMap: typeof window.initializeprojectMap,
    loadProjectMarkers: typeof window.loadProjectMarkers,
    centerMapOnPhilippines: typeof window.centerMapOnPhilippines,
    closeProjectPopup: typeof window.closeProjectPopup
});