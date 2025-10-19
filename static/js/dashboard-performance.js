// Dashboard Performance Optimizations and Production Enhancements

// Performance monitoring and optimization utilities
class DashboardPerformanceMonitor {
    constructor() {
        this.metrics = {
            pageLoadTime: 0,
            chartRenderTime: 0,
            mapLoadTime: 0,
            totalMemoryUsage: 0
        };
        this.init();
    }

    init() {
        this.trackPageLoad();
        this.setupIntersectionObserver();
        this.setupErrorReporting();
        this.setupMemoryMonitoring();

        // Log performance metrics in development
        if (this.isDevelopment()) {
            this.logPerformanceMetrics();
        }
    }

    trackPageLoad() {
        window.addEventListener('load', () => {
            if (performance.timing && performance.timing.loadEventEnd > 0 && performance.timing.navigationStart > 0) {
                this.metrics.pageLoadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
                console.log(`Dashboard loaded in ${this.metrics.pageLoadTime}ms`);
            } else if (performance.now) {
                this.metrics.pageLoadTime = Math.round(performance.now());
                console.log(`Dashboard loaded in ${this.metrics.pageLoadTime}ms`);
            }
        });
    }

    setupIntersectionObserver() {
        // Lazy load charts and heavy components
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const element = entry.target;

                    // Load chart when it comes into view
                    if (element.id === 'progressChart' && !window.progressChart) {
                        this.loadChartAsync('progress');
                    }

                    if (element.id === 'budgetChart' && !window.budgetChart) {
                        this.loadChartAsync('budget');
                    }

                    observer.unobserve(element);
                }
            });
        }, {
            rootMargin: '50px'
        });

        // Observe chart containers
        const chartElements = document.querySelectorAll('#progressChart, #budgetChart');
        chartElements.forEach(el => observer.observe(el));
    }

    async loadChartAsync(type) {
        const startTime = performance.now();

        try {
            // Dynamic import for Chart.js if not already loaded
            if (!window.Chart) {
                await this.loadScript('https://cdn.jsdelivr.net/npm/chart.js');
            }

            // Initialize specific chart
            if (type === 'progress' && window.initializeProgressChart) {
                window.initializeProgressChart(window.dashboardData?.projects || []);
            } else if (type === 'budget' && window.initializeBudgetChart) {
                window.initializeBudgetChart(window.dashboardData?.projects || []);
            }

            const endTime = performance.now();
            this.metrics.chartRenderTime = endTime - startTime;

        } catch (error) {
            console.error(`Failed to load ${type} chart:`, error);
        }
    }

    setupErrorReporting() {
        window.addEventListener('error', (event) => {
            this.reportError({
                type: 'javascript',
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                stack: event.error?.stack
            });
        });

        window.addEventListener('unhandledrejection', (event) => {
            this.reportError({
                type: 'promise',
                message: event.reason?.message || 'Unhandled Promise Rejection',
                stack: event.reason?.stack
            });
        });
    }

    setupMemoryMonitoring() {
        if (performance.memory) {
            setInterval(() => {
                this.metrics.totalMemoryUsage = performance.memory.usedJSHeapSize;

                // Warn if memory usage exceeds 50MB
                if (this.metrics.totalMemoryUsage > 50 * 1024 * 1024) {
                    console.warn('High memory usage detected:', this.formatBytes(this.metrics.totalMemoryUsage));
                }
            }, 30000); // Check every 30 seconds
        }
    }

    reportError(errorData) {
        // In production, send to error reporting service
        if (this.isProduction()) {
            // Replace with your error reporting service
            // fetch('/api/errors/', { method: 'POST', body: JSON.stringify(errorData) });
        } else {
            console.error('Dashboard Error:', errorData);
        }
    }

    loadScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    isDevelopment() {
        return window.location.hostname === 'localhost' ||
               window.location.hostname === '127.0.0.1' ||
               window.location.hostname.includes('dev');
    }

    isProduction() {
        return !this.isDevelopment();
    }

    logPerformanceMetrics() {
        setTimeout(() => {
            console.group('📊 Dashboard Performance Metrics');
            console.log('Page Load Time:', this.metrics.pageLoadTime + 'ms');
            console.log('Chart Render Time:', this.metrics.chartRenderTime + 'ms');
            console.log('Map Load Time:', this.metrics.mapLoadTime + 'ms');
            if (performance.memory) {
                console.log('Memory Usage:', this.formatBytes(performance.memory.usedJSHeapSize));
                console.log('Memory Limit:', this.formatBytes(performance.memory.jsHeapSizeLimit));
            }
            console.groupEnd();
        }, 2000);
    }

    getMetrics() {
        return {
            ...this.metrics,
            memoryFormatted: performance.memory ? this.formatBytes(performance.memory.usedJSHeapSize) : 'N/A'
        };
    }
}

// Service Worker registration for offline support
class DashboardServiceWorker {
    constructor() {
        this.init();
    }

    async init() {
        if ('serviceWorker' in navigator && this.isProduction()) {
            try {
                const registration = await navigator.serviceWorker.register('/sw.js');
                console.log('Service Worker registered:', registration);

                registration.addEventListener('updatefound', () => {
                    this.showUpdateNotification();
                });
            } catch (error) {
                console.log('Service Worker registration failed:', error);
            }
        }
    }

    showUpdateNotification() {
        // Show user-friendly update notification
        const notification = document.createElement('div');
        notification.className = 'fixed bottom-4 right-4 bg-blue-600 text-white p-4 rounded-lg shadow-lg z-50';
        notification.innerHTML = `
            <div class="flex items-center space-x-3">
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"></path>
                </svg>
                <div>
                    <p class="font-medium">Dashboard Update Available</p>
                    <button onclick="window.location.reload()" class="text-sm underline">Refresh to update</button>
                </div>
            </div>
        `;
        document.body.appendChild(notification);
    }

    isProduction() {
        return window.location.hostname !== 'localhost' &&
               window.location.hostname !== '127.0.0.1';
    }
}

// Image optimization and lazy loading
class ImageOptimizer {
    constructor() {
        this.init();
    }

    init() {
        this.setupLazyLoading();
        this.setupImageCompression();
    }

    setupLazyLoading() {
        const images = document.querySelectorAll('img[data-src]');

        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });

        images.forEach(img => imageObserver.observe(img));
    }

    setupImageCompression() {
        // Automatically convert high-resolution images to appropriate formats
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            if (img.src && !img.src.includes('optimized')) {
                this.optimizeImage(img);
            }
        });
    }

    optimizeImage(img) {
        // In production, use a service like Cloudinary or ImageKit
        // This is a placeholder for image optimization logic
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        img.onload = () => {
            const maxWidth = 800;
            const maxHeight = 600;

            let { width, height } = img;

            if (width > maxWidth || height > maxHeight) {
                const ratio = Math.min(maxWidth / width, maxHeight / height);
                width *= ratio;
                height *= ratio;
            }

            canvas.width = width;
            canvas.height = height;

            ctx.drawImage(img, 0, 0, width, height);

            canvas.toBlob((blob) => {
                if (blob && blob.size < img.size) {
                    img.src = URL.createObjectURL(blob);
                }
            }, 'image/jpeg', 0.8);
        };
    }
}

// Cache management for better performance
class DashboardCacheManager {
    constructor() {
        this.cachePrefix = 'dashboard_';
        this.cacheDuration = 5 * 60 * 1000; // 5 minutes
        this.init();
    }

    init() {
        this.cleanExpiredCache();
        this.setupCacheInterceptor();
    }

    set(key, data, customDuration = null) {
        const item = {
            data: data,
            timestamp: Date.now(),
            duration: customDuration || this.cacheDuration
        };

        try {
            localStorage.setItem(this.cachePrefix + key, JSON.stringify(item));
        } catch (error) {
            console.warn('Cache storage failed:', error);
        }
    }

    get(key) {
        try {
            const item = localStorage.getItem(this.cachePrefix + key);
            if (!item) return null;

            const parsed = JSON.parse(item);

            if (Date.now() - parsed.timestamp > parsed.duration) {
                localStorage.removeItem(this.cachePrefix + key);
                return null;
            }

            return parsed.data;
        } catch (error) {
            console.warn('Cache retrieval failed:', error);
            return null;
        }
    }

    cleanExpiredCache() {
        Object.keys(localStorage).forEach(key => {
            if (key.startsWith(this.cachePrefix)) {
                try {
                    const item = JSON.parse(localStorage.getItem(key));
                    if (Date.now() - item.timestamp > item.duration) {
                        localStorage.removeItem(key);
                    }
                } catch (error) {
                    localStorage.removeItem(key);
                }
            }
        });
    }

    setupCacheInterceptor() {
        // Intercept dashboard API calls and cache responses
        const originalFetch = window.fetch;
        window.fetch = async (url, options = {}) => {
            if (url.includes('/api/dashboard/') && options.method !== 'POST') {
                const cacheKey = 'api_' + url;
                const cached = this.get(cacheKey);

                if (cached) {
                    return new Response(JSON.stringify(cached), {
                        status: 200,
                        headers: { 'Content-Type': 'application/json' }
                    });
                }

                const response = await originalFetch(url, options);
                if (response.ok) {
                    const data = await response.clone().json();
                    this.set(cacheKey, data);
                }

                return response;
            }

            return originalFetch(url, options);
        };
    }
}

// Initialize performance monitoring and optimizations
document.addEventListener('DOMContentLoaded', () => {
    // Initialize performance monitoring
    window.dashboardPerformance = new DashboardPerformanceMonitor();

    // Initialize service worker
    window.dashboardSW = new DashboardServiceWorker();

    // Initialize image optimization
    window.imageOptimizer = new ImageOptimizer();

    // Initialize cache management
    window.cacheManager = new DashboardCacheManager();

    // Add global error boundary
    window.addEventListener('error', (event) => {
        console.error('Global error caught:', event.error);

        // Show user-friendly error message
        const errorNotification = document.createElement('div');
        errorNotification.className = 'fixed top-4 left-4 bg-red-500 text-white p-4 rounded-lg shadow-lg z-50 max-w-md';
        errorNotification.innerHTML = `
            <div class="flex items-center space-x-2">
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                </svg>
                <div>
                    <p class="font-medium">Something went wrong</p>
                    <p class="text-sm">Please refresh the page</p>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-auto text-white hover:text-gray-200">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                    </svg>
                </button>
            </div>
        `;

        document.body.appendChild(errorNotification);

        // Auto remove after 10 seconds
        setTimeout(() => {
            errorNotification.remove();
        }, 10000);
    });

    console.log('🚀 Dashboard performance optimizations loaded');
});

// Export for testing and debugging
window.DashboardPerformance = {
    monitor: () => window.dashboardPerformance,
    cache: () => window.cacheManager,
    metrics: () => window.dashboardPerformance?.getMetrics()
};