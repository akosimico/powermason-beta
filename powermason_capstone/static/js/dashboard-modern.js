// Modern Dashboard with Mapbox GL JS Integration
// Enhanced UI/UX with smooth animations and production-ready features

// ====================================================================
// CONFIGURATION & INITIALIZATION
// ====================================================================

// Global configuration
window.DASHBOARD_CONFIG = window.DASHBOARD_CONFIG || {
    animations: true,
    autoRefresh: true,
    mapStyle: 'satellite-streets',
    theme: 'modern'
};

// Mapbox configuration
mapboxgl.accessToken = window.MAPBOX_TOKEN || 'pk.eyJ1IjoicG93ZXJtYXNvbiIsImEiOiJjbTRleDc0YjUwcW83MmxzYzJqY2dwc3VoIn0.vZODcJ4QGUi9y0_Gm8vLWw';

// Global variables
let map = null;
let markers = [];
let currentMapStyle = 'mapbox://styles/mapbox/satellite-streets-v12';
let isMapInitialized = false;

// Philippines bounds and center
const PHILIPPINES_BOUNDS = [
    [116.0, 4.5],   // Southwest
    [127.0, 21.5]   // Northeast
];
const PHILIPPINES_CENTER = [121.7740, 12.8797]; // [lng, lat] for Mapbox

// Project status configuration
const STATUS_CONFIG = {
    'PL': {
        color: '#3b82f6',
        name: 'Planned',
        icon: '●',
        gradient: 'from-blue-500 to-blue-600'
    },
    'OG': {
        color: '#f97316',
        name: 'In Progress',
        icon: '▶',
        gradient: 'from-orange-500 to-orange-600'
    },
    'IP': {
        color: '#f97316',
        name: 'In Progress',
        icon: '▶',
        gradient: 'from-orange-500 to-orange-600'
    },
    'CP': {
        color: '#22c55e',
        name: 'Completed',
        icon: '✓',
        gradient: 'from-green-500 to-green-600'
    },
    'CN': {
        color: '#ef4444',
        name: 'Cancelled',
        icon: '✕',
        gradient: 'from-red-500 to-red-600'
    }
};

// Map styles for toggling
const MAP_STYLES = {
    'satellite-streets': 'mapbox://styles/mapbox/satellite-streets-v12',
    'streets': 'mapbox://styles/mapbox/streets-v12',
    'light': 'mapbox://styles/mapbox/light-v11',
    'dark': 'mapbox://styles/mapbox/dark-v11'
};

// ====================================================================
// UTILITY FUNCTIONS
// ====================================================================

function showToast(message, type = 'info', duration = 3000) {
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

    setTimeout(() => {
        toast.style.transform = 'translateX(100%)';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 500);
    }, duration);
}

function animateCounter(element, start, end, duration = 1000) {
    if (!element) return;

    const startTime = Date.now();
    const difference = end - start;

    function update() {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Easing function for smooth animation
        const easeOutCubic = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(start + (difference * easeOutCubic));

        element.textContent = current.toLocaleString();

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    update();
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

// ====================================================================
// MAPBOX INTEGRATION
// ====================================================================

function initializeMap() {
    console.log('Initializing Mapbox map...');

    const mapContainer = document.getElementById('projectsMap');
    if (!mapContainer) {
        console.error('Map container not found');
        return;
    }

    // Clear any existing content first
    mapContainer.innerHTML = '';

    try {
        // Initialize Mapbox map
        map = new mapboxgl.Map({
            container: 'projectsMap',
            style: currentMapStyle,
            center: PHILIPPINES_CENTER,
            zoom: 5.5,
            maxBounds: PHILIPPINES_BOUNDS,
            pitch: 0,
            bearing: 0,
            antialias: true,
            optimizeForTerrain: true,
            // Explicitly enable interactive controls
            dragPan: true,
            scrollZoom: true,
            boxZoom: true,
            dragRotate: true,
            keyboard: true,
            doubleClickZoom: true,
            touchZoomRotate: true,
            interactive: true
        });

        // Add navigation controls
        const nav = new mapboxgl.NavigationControl({
            visualizePitch: true,
            showZoom: true,
            showCompass: true
        });
        map.addControl(nav, 'top-left');

        // Add fullscreen control
        map.addControl(new mapboxgl.FullscreenControl(), 'top-left');

        // Add scale control
        map.addControl(new mapboxgl.ScaleControl({
            maxWidth: 100,
            unit: 'metric'
        }), 'bottom-left');

        // Map load event
        map.on('load', () => {
            console.log('Map loaded successfully');
            isMapInitialized = true;

            // Ensure all interactive controls are enabled after load
            map.dragPan.enable();
            map.scrollZoom.enable();
            map.boxZoom.enable();
            map.dragRotate.enable();
            map.keyboard.enable();
            map.doubleClickZoom.enable();
            map.touchZoomRotate.enable();

            // Force enable interactions and fix canvas
            setTimeout(() => {
                const mapContainer = document.getElementById('projectsMap');
                const mapCanvas = map.getCanvas();

                if (mapContainer) {
                    // Ensure container allows interactions
                    mapContainer.style.pointerEvents = 'auto !important';
                    mapContainer.style.touchAction = 'manipulation';
                    mapContainer.style.cursor = 'grab';
                    mapContainer.style.userSelect = 'none';
                    mapContainer.style.position = 'relative';
                    mapContainer.style.zIndex = '1';
                }

                if (mapCanvas) {
                    // Ensure canvas receives mouse events
                    mapCanvas.style.pointerEvents = 'auto !important';
                    mapCanvas.style.touchAction = 'manipulation';
                    mapCanvas.style.cursor = 'grab';
                    mapCanvas.style.userSelect = 'none';

                    // Force focus to enable keyboard interactions
                    mapCanvas.tabIndex = 0;

                    // Remove any conflicting event listeners that might prevent interaction
                    mapCanvas.style.webkitUserSelect = 'none';
                    mapCanvas.style.mozUserSelect = 'none';
                    mapCanvas.style.msUserSelect = 'none';

                    // Ensure canvas is positioned correctly
                    mapCanvas.style.position = 'relative';
                    mapCanvas.style.zIndex = '1';

                    // Add test event listener to verify canvas receives events
                    mapCanvas.addEventListener('mousedown', function(e) {
                        console.log('🖱️ Canvas mousedown detected at:', e.clientX, e.clientY);
                    }, { passive: true });

                    mapCanvas.addEventListener('wheel', function(e) {
                        console.log('🎯 Canvas wheel detected');
                    }, { passive: true });

                    console.log('Map canvas configured for interactions');
                }

                // Double-check all interactions are enabled
                map.dragPan.enable();
                map.scrollZoom.enable();
                map.boxZoom.enable();
                map.dragRotate.enable();
                map.keyboard.enable();
                map.doubleClickZoom.enable();
                map.touchZoomRotate.enable();

                // Force resize to ensure proper display
                map.resize();
                console.log('Map fully configured - dragPan:', map.dragPan.isEnabled(), 'scrollZoom:', map.scrollZoom.isEnabled());

            }, 200);

            loadProjectMarkers();
            showToast('Interactive map loaded', 'success');

            // Add interaction event handlers for debugging
            map.on('dragstart', () => console.log('✅ Map drag started'));
            map.on('drag', () => console.log('🖱️ Map dragging'));
            map.on('dragend', () => console.log('✅ Map drag ended'));
            map.on('wheel', () => console.log('🎯 Map wheel zoom'));
            map.on('mousedown', () => console.log('👇 Map mouse down'));
            map.on('mouseup', () => console.log('👆 Map mouse up'));
            map.on('touchstart', () => console.log('👆 Map touch start'));
            map.on('zoomstart', () => console.log('🔍 Map zoom start'));
            map.on('zoomend', () => console.log('🔍 Map zoom end'));
        });

        // Add cursor change handlers
        map.on('mouseenter', () => {
            map.getCanvas().style.cursor = 'grab';
        });

        map.on('mousedown', () => {
            map.getCanvas().style.cursor = 'grabbing';
        });

        map.on('mouseup', () => {
            map.getCanvas().style.cursor = 'grab';
        });

        // Map error handling
        map.on('error', (e) => {
            console.error('Map error:', e);
            showToast('Map failed to load', 'error');
        });

        // Map style load event
        map.on('style.load', () => {
            console.log('Map style loaded');
            if (isMapInitialized) {
                loadProjectMarkers();
            }
        });

        // Add comprehensive map interaction fix
        window.forceEnableMapInteractions = function() {
            console.log('🔧 Force enabling all map interactions...');

            // Disable and re-enable all handlers to reset them
            map.dragPan.disable();
            map.scrollZoom.disable();
            map.boxZoom.disable();
            map.dragRotate.disable();
            map.keyboard.disable();
            map.doubleClickZoom.disable();
            map.touchZoomRotate.disable();

            setTimeout(() => {
                map.dragPan.enable();
                map.scrollZoom.enable();
                map.boxZoom.enable();
                map.dragRotate.enable();
                map.keyboard.enable();
                map.doubleClickZoom.enable();
                map.touchZoomRotate.enable();

                console.log('✅ All interactions re-enabled');
                window.testMapInteractions();
            }, 100);
        };

        // Add a test function to verify map interactions
        window.testMapInteractions = function() {
            console.log('🧪 Testing map interactions...');
            console.log('- dragPan enabled:', map.dragPan.isEnabled());
            console.log('- scrollZoom enabled:', map.scrollZoom.isEnabled());
            console.log('- boxZoom enabled:', map.boxZoom.isEnabled());
            console.log('- dragRotate enabled:', map.dragRotate.isEnabled());
            console.log('- keyboard enabled:', map.keyboard.isEnabled());
            console.log('- doubleClickZoom enabled:', map.doubleClickZoom.isEnabled());
            console.log('- touchZoomRotate enabled:', map.touchZoomRotate.isEnabled());

            const canvas = map.getCanvas();
            console.log('- Canvas pointer events:', getComputedStyle(canvas).pointerEvents);
            console.log('- Canvas touch action:', getComputedStyle(canvas).touchAction);
            console.log('- Canvas cursor:', getComputedStyle(canvas).cursor);

            const container = document.getElementById('projectsMap');
            console.log('- Container pointer events:', getComputedStyle(container).pointerEvents);
            console.log('- Container touch action:', getComputedStyle(container).touchAction);
            console.log('- Container position:', getComputedStyle(container).position);

            // Test programmatic pan
            console.log('🧪 Testing programmatic map movement...');
            const currentCenter = map.getCenter();
            map.panBy([50, 50]);
            setTimeout(() => {
                map.setCenter(currentCenter);
                console.log('✅ Programmatic movement test completed');
            }, 1000);
        };

        // Force enable interactions after a delay to ensure everything is loaded
        setTimeout(() => {
            window.forceEnableMapInteractions();
        }, 500);

        console.log('Mapbox map initialized - Run window.testMapInteractions() to test');

    } catch (error) {
        console.error('Error initializing map:', error);
        showMapError(error.message);
    }
}

function showMapError(message) {
    const mapContainer = document.getElementById('projectsMap');
    if (mapContainer) {
        mapContainer.innerHTML = `
            <div class="flex items-center justify-center h-full bg-gradient-to-br from-red-50 to-red-100 rounded-2xl border-2 border-red-200">
                <div class="text-center p-8">
                    <div class="text-6xl mb-4">🗺️</div>
                    <h3 class="text-lg font-bold text-red-800 mb-2">Map Loading Failed</h3>
                    <p class="text-sm text-red-600 mb-4">${message}</p>
                    <button onclick="initializeMap()" class="px-4 py-2 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg hover:from-red-600 hover:to-red-700 transition-all duration-200 font-medium">
                        Retry Loading
                    </button>
                </div>
            </div>
        `;
    }
}

function loadProjectMarkers() {
    if (!map || !isMapInitialized) {
        console.warn('Map not ready for markers');
        return;
    }

    console.log('Loading project markers...');

    // Clear existing markers
    markers.forEach(marker => marker.remove());
    markers = [];

    // Get project data
    let projectsData = [];

    if (window.dashboardData?.projects) {
        projectsData = window.dashboardData.projects;
    } else {
        const projectsDataScript = document.getElementById('projects-data');
        if (projectsDataScript && projectsDataScript.textContent.trim()) {
            try {
                projectsData = JSON.parse(projectsDataScript.textContent);
            } catch (error) {
                console.error('Error parsing projects data:', error);
                return;
            }
        } else {
            console.warn('No projects data found, adding sample markers');
            addSampleMarkers();
            return;
        }
    }

    if (!Array.isArray(projectsData) || projectsData.length === 0) {
        console.warn('No project data available, adding sample markers');
        addSampleMarkers();
        return;
    }

    let markersAdded = 0;
    let statusCounts = {
        'PL': 0, 'OG': 0, 'IP': 0, 'CP': 0, 'CN': 0
    };

    // Process each project
    projectsData.forEach((project, index) => {
        try {
            const status = project.status || 'PL';
            statusCounts[status] = (statusCounts[status] || 0) + 1;

            const gpsCoords = project.gps_coordinates ||
                             project.coordinates ||
                             project.location_coordinates ||
                             project.lat_lng;

            if (gpsCoords) {
                const coords = gpsCoords.toString().split(',');
                if (coords.length >= 2) {
                    const lat = parseFloat(coords[0].trim());
                    const lng = parseFloat(coords[1].trim());

                    if (!isNaN(lat) && !isNaN(lng) &&
                        lat >= -90 && lat <= 90 &&
                        lng >= -180 && lng <= 180) {

                        addProjectMarker(project, lng, lat); // Note: Mapbox uses [lng, lat]
                        markersAdded++;
                    }
                }
            }
        } catch (error) {
            console.error(`Error processing project ${index}:`, error);
        }
    });

    console.log(`Added ${markersAdded} markers to map`);
    updateMapStats(projectsData.length, markersAdded, statusCounts.OG + statusCounts.IP);
    updateStatusCounts(statusCounts);

    if (markersAdded === 0) {
        addSampleMarkers();
    }
}

function addProjectMarker(project, lng, lat) {
    const status = project.status || 'PL';
    const config = STATUS_CONFIG[status] || STATUS_CONFIG['PL'];

    // Create custom marker element
    const markerElement = document.createElement('div');
    markerElement.className = 'project-marker';
    markerElement.innerHTML = `
        <div class="w-8 h-8 rounded-full border-2 border-white shadow-lg cursor-pointer transition-all duration-300 hover:scale-125 flex items-center justify-center text-white font-bold text-sm"
             style="background: linear-gradient(135deg, ${config.color}, ${config.color}dd);">
            ${config.icon}
        </div>
    `;

    // Create marker
    const marker = new mapboxgl.Marker(markerElement)
        .setLngLat([lng, lat])
        .addTo(map);

    // Create popup
    const popup = new mapboxgl.Popup({
        offset: 25,
        closeButton: true,
        closeOnClick: false,
        className: 'project-popup'
    }).setHTML(createPopupContent(project));

    // Add click event
    markerElement.addEventListener('click', () => {
        popup.addTo(map);
        marker.setPopup(popup);
        marker.togglePopup();
    });

    markers.push(marker);
}

function createPopupContent(project) {
    const status = project.status || 'PL';
    const config = STATUS_CONFIG[status] || STATUS_CONFIG['PL'];

    return `
        <div class="p-4 min-w-[280px]">
            <div class="flex items-center space-x-3 mb-3">
                <div class="w-10 h-10 rounded-full bg-gradient-to-br ${config.gradient} flex items-center justify-center text-white font-bold shadow-lg">
                    ${config.icon}
                </div>
                <div>
                    <h3 class="font-bold text-lg text-gray-800">${project.project_name || project.name || 'Unnamed Project'}</h3>
                    <span class="inline-block px-2 py-1 bg-gradient-to-r ${config.gradient} text-white text-xs rounded-full font-medium">
                        ${config.name}
                    </span>
                </div>
            </div>

            <div class="space-y-2 text-sm">
                ${project.location ? `
                <div class="flex items-center space-x-2">
                    <svg class="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd"></path>
                    </svg>
                    <span class="text-gray-700">${project.location}</span>
                </div>
                ` : ''}

                ${project.client_name ? `
                <div class="flex items-center space-x-2">
                    <svg class="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"></path>
                    </svg>
                    <span class="text-gray-700">${project.client_name}</span>
                </div>
                ` : ''}

                ${project.estimated_cost ? `
                <div class="flex items-center space-x-2">
                    <svg class="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z"></path>
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clip-rule="evenodd"></path>
                    </svg>
                    <span class="text-gray-700">₱${parseFloat(project.estimated_cost).toLocaleString()}</span>
                </div>
                ` : ''}

                ${project.start_date ? `
                <div class="flex items-center space-x-2">
                    <svg class="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clip-rule="evenodd"></path>
                    </svg>
                    <span class="text-gray-700">${formatDate(project.start_date)}</span>
                </div>
                ` : ''}
            </div>

            ${project.view_url ? `
            <div class="mt-4 pt-3 border-t border-gray-200">
                <a href="${project.view_url}" target="_blank"
                   class="inline-flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg hover:from-blue-600 hover:to-blue-700 transition-all duration-200 font-medium text-sm">
                    <span>View Details</span>
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                    </svg>
                </a>
            </div>
            ` : ''}
        </div>
    `;
}

function addSampleMarkers() {
    console.log('Adding sample markers...');

    const sampleProjects = [
        {
            project_name: "Manila Business District",
            status: "OG",
            location: "Makati, Manila",
            client_name: "Metro Development Corp",
            estimated_cost: 15000000,
            start_date: "2024-01-15"
        },
        {
            project_name: "Cebu Resort Complex",
            status: "PL",
            location: "Cebu City, Cebu",
            client_name: "Island Resort Holdings",
            estimated_cost: 25000000,
            start_date: "2024-06-01"
        },
        {
            project_name: "Davao Convention Center",
            status: "CP",
            location: "Davao City, Davao",
            client_name: "Southern Events Corp",
            estimated_cost: 18000000,
            start_date: "2023-08-01"
        },
        {
            project_name: "Baguio Eco Lodge",
            status: "PL",
            location: "Baguio City, Benguet",
            client_name: "Mountain View Resorts",
            estimated_cost: 12000000,
            start_date: "2024-09-01"
        },
        {
            project_name: "Palawan Marine Center",
            status: "OG",
            location: "Puerto Princesa, Palawan",
            client_name: "Marine Conservation Group",
            estimated_cost: 8000000,
            start_date: "2024-02-15"
        }
    ];

    const sampleCoordinates = [
        [121.0244, 14.5547], // Manila
        [123.8854, 10.3157], // Cebu
        [125.4553, 7.1907],  // Davao
        [120.5960, 16.4023], // Baguio
        [118.7500, 9.7500]   // Puerto Princesa
    ];

    sampleProjects.forEach((project, index) => {
        const [lng, lat] = sampleCoordinates[index];
        addProjectMarker(project, lng, lat);
    });

    const statusCounts = {
        'PL': 2, 'OG': 2, 'CP': 1, 'CN': 0
    };

    updateMapStats(sampleProjects.length, sampleProjects.length, 2);
    updateStatusCounts(statusCounts);
}

// ====================================================================
// MAP CONTROLS
// ====================================================================

function centerMapOnPhilippines() {
    if (map) {
        map.flyTo({
            center: PHILIPPINES_CENTER,
            zoom: 5.5,
            essential: true,
            duration: 2000
        });
        showToast('Map centered on Philippines', 'info', 2000);
    }
}

function toggleMapStyle() {
    if (!map) return;

    const styleKeys = Object.keys(MAP_STYLES);
    const currentStyleIndex = styleKeys.findIndex(key => MAP_STYLES[key] === currentMapStyle);
    const nextStyleIndex = (currentStyleIndex + 1) % styleKeys.length;
    const nextStyleKey = styleKeys[nextStyleIndex];

    currentMapStyle = MAP_STYLES[nextStyleKey];
    map.setStyle(currentMapStyle);

    const styleNames = {
        'satellite-streets': 'Satellite',
        'streets': 'Streets',
        'light': 'Light',
        'dark': 'Dark'
    };

    showToast(`Switched to ${styleNames[nextStyleKey]} style`, 'info', 2000);
}

// ====================================================================
// UI UPDATES
// ====================================================================

function updateMapStats(totalProjects, mappedProjects, activeProjects) {
    animateCounter(document.getElementById('totalProjectsCount'), 0, totalProjects);
    animateCounter(document.getElementById('mappedProjectsCount'), 0, mappedProjects);
    animateCounter(document.getElementById('activeProjectsCount'), 0, activeProjects);
}

function updateStatusCounts(statusCounts) {
    animateCounter(document.getElementById('planned-count'), 0, statusCounts.PL || 0);
    animateCounter(document.getElementById('progress-count'), 0, (statusCounts.OG || 0) + (statusCounts.IP || 0));
    animateCounter(document.getElementById('completed-count'), 0, statusCounts.CP || 0);
    animateCounter(document.getElementById('cancelled-count'), 0, statusCounts.CN || 0);
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

// ====================================================================
// DASHBOARD INITIALIZATION
// ====================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('Modern dashboard initializing...');

    // Show initial loading message
    showToast('Loading modern dashboard...', 'info', 2000);

    // Initialize map with a slight delay to ensure DOM is ready
    setTimeout(() => {
        if (typeof mapboxgl !== 'undefined') {
            initializeMap();
        } else {
            console.error('Mapbox GL JS not loaded');
            showToast('Map library failed to load', 'error');
        }
    }, 500);

    // Initialize other dashboard components
    initializeCharts();
    initializeCalendar();

    console.log('Modern dashboard initialized');
});

// Handle page resize
window.addEventListener('resize', debounce(() => {
    if (map) {
        map.resize();
    }
}, 250));

// ====================================================================
// GLOBAL EXPORTS
// ====================================================================

// Make functions globally available
window.initializeMapModern = initializeMap;
window.centerMapOnPhilippines = centerMapOnPhilippines;
window.toggleMapStyle = toggleMapStyle;
window.loadProjectMarkers = loadProjectMarkers;

// Debug utilities
window.mapDebug = {
    map: () => map,
    markers: () => markers,
    config: () => window.DASHBOARD_CONFIG,
    reinitialize: () => {
        if (map) {
            map.remove();
            map = null;
            isMapInitialized = false;
        }
        initializeMap();
    },
    addTestMarker: (lng, lat, name = 'Test Marker') => {
        const testProject = {
            project_name: name,
            status: 'OG',
            location: 'Test Location',
            client_name: 'Test Client'
        };
        addProjectMarker(testProject, lng, lat);
    }
};

console.log('Modern Mapbox dashboard loaded successfully!');
console.log('Available debug utilities: window.mapDebug');