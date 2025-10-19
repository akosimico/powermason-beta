/**
 * AJAX Navigation System for PowerMason
 * Provides seamless navigation between modules without page reloads
 */

class AjaxNavigation {
    constructor() {
        this.currentUrl = window.location.pathname;
        this.isNavigating = false;
        this.cache = new Map();
        this.loadingOverlay = null;
        this.init();
    }

    init() {
        console.log('🚀 Initializing AJAX Navigation...');
        this.createSkeletonLoader();
        this.bindEvents();
        this.setupHistoryAPI();
        this.initializeActiveStates();
        
        // Stop any dashboard auto-refresh when navigating away from dashboard
        this.stopDashboardAutoRefresh();
        
        console.log('✅ AJAX Navigation fully initialized');
    }

    createSkeletonLoader() {
        // Create skeleton loading container
        this.skeletonContainer = document.createElement('div');
        this.skeletonContainer.id = 'skeleton-loader';
        this.skeletonContainer.className = 'hidden';
        this.skeletonContainer.innerHTML = `
            <div class="animate-pulse space-y-6 p-6">
                <!-- Header skeleton -->
                <div class="space-y-3">
                    <div class="h-8 bg-gray-300 rounded-lg w-1/3 animate-pulse"></div>
                    <div class="h-4 bg-gray-300 rounded w-1/2 animate-pulse"></div>
                </div>
                
                <!-- Stats Cards skeleton -->
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                        <div class="space-y-3">
                            <div class="h-4 bg-gray-300 rounded w-3/4 animate-pulse"></div>
                            <div class="h-8 bg-gray-300 rounded w-1/2 animate-pulse"></div>
                        </div>
                    </div>
                    <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                        <div class="space-y-3">
                            <div class="h-4 bg-gray-300 rounded w-3/4 animate-pulse"></div>
                            <div class="h-8 bg-gray-300 rounded w-1/2 animate-pulse"></div>
                        </div>
                    </div>
                    <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                        <div class="space-y-3">
                            <div class="h-4 bg-gray-300 rounded w-3/4 animate-pulse"></div>
                            <div class="h-8 bg-gray-300 rounded w-1/2 animate-pulse"></div>
                        </div>
                    </div>
                    <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                        <div class="space-y-3">
                            <div class="h-4 bg-gray-300 rounded w-3/4 animate-pulse"></div>
                            <div class="h-8 bg-gray-300 rounded w-1/2 animate-pulse"></div>
                        </div>
                    </div>
                </div>
                
                <!-- Search/Filter skeleton -->
                <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div class="md:col-span-2 space-y-2">
                            <div class="h-4 bg-gray-300 rounded w-1/4 animate-pulse"></div>
                            <div class="h-10 bg-gray-300 rounded animate-pulse"></div>
                        </div>
                        <div class="space-y-2">
                            <div class="h-4 bg-gray-300 rounded w-1/3 animate-pulse"></div>
                            <div class="h-10 bg-gray-300 rounded animate-pulse"></div>
                        </div>
                        <div class="flex items-end">
                            <div class="h-10 bg-gray-300 rounded w-full animate-pulse"></div>
                        </div>
                    </div>
                </div>
                
                <!-- Table skeleton -->
                <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                    <div class="p-6 border-b border-gray-200">
                        <div class="h-6 bg-gray-300 rounded w-1/4 animate-pulse"></div>
                    </div>
                    <div class="p-6 space-y-4">
                        <div class="flex space-x-4">
                            <div class="h-4 bg-gray-300 rounded flex-1 animate-pulse"></div>
                            <div class="h-4 bg-gray-300 rounded w-24 animate-pulse"></div>
                            <div class="h-4 bg-gray-300 rounded w-20 animate-pulse"></div>
                        </div>
                        <div class="flex space-x-4">
                            <div class="h-4 bg-gray-300 rounded flex-1 animate-pulse"></div>
                            <div class="h-4 bg-gray-300 rounded w-24 animate-pulse"></div>
                            <div class="h-4 bg-gray-300 rounded w-20 animate-pulse"></div>
                        </div>
                        <div class="flex space-x-4">
                            <div class="h-4 bg-gray-300 rounded flex-1 animate-pulse"></div>
                            <div class="h-4 bg-gray-300 rounded w-24 animate-pulse"></div>
                            <div class="h-4 bg-gray-300 rounded w-20 animate-pulse"></div>
                        </div>
                        <div class="flex space-x-4">
                            <div class="h-4 bg-gray-300 rounded flex-1 animate-pulse"></div>
                            <div class="h-4 bg-gray-300 rounded w-24 animate-pulse"></div>
                            <div class="h-4 bg-gray-300 rounded w-20 animate-pulse"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(this.skeletonContainer);
    }

    bindEvents() {
        // Intercept all internal links
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href]');
            if (!link) return;

            const href = link.getAttribute('href');
            
            // Skip if it's an external link, mailto, tel, or has special attributes
            if (this.shouldSkipLink(link, href)) {
                return;
            }

            // Skip if it's a form submission link
            if (link.hasAttribute('data-form-submit')) {
                return;
            }

            // Skip if it's a download link
            if (link.hasAttribute('download') || href.includes('/download/') || href.includes('/export/')) {
                return;
            }

            // Skip if it's a modal trigger
            if (link.hasAttribute('data-modal') || link.hasAttribute('data-toggle')) {
                return;
            }

            e.preventDefault();
            this.navigate(href, link);
        });

        // Handle form submissions
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.hasAttribute('data-ajax-form')) {
                e.preventDefault();
                this.submitForm(form);
            }
        });

        // Handle back/forward buttons
        window.addEventListener('popstate', (e) => {
            if (e.state && e.state.ajax) {
                this.loadPage(e.state.url, false);
            }
        });
    }

    shouldSkipLink(link, href) {
        // Skip external links
        if (href.startsWith('http') && !href.includes(window.location.hostname)) {
            return true;
        }

        // Skip special protocols
        if (href.startsWith('mailto:') || href.startsWith('tel:') || href.startsWith('javascript:')) {
            return true;
        }

        // Skip if it's the same page
        if (href === this.currentUrl || href === window.location.href) {
            return true;
        }

        // Skip if it has data-skip-ajax attribute
        if (link.hasAttribute('data-skip-ajax')) {
            return true;
        }

        // Skip if it's a hash link
        if (href.startsWith('#')) {
            return true;
        }

        // Skip if it's a form submission or download
        if (link.hasAttribute('download') || link.hasAttribute('data-form-submit')) {
            return true;
        }

        // Skip if it's a modal trigger
        if (link.hasAttribute('data-modal') || link.hasAttribute('data-toggle')) {
            return true;
        }

        // Skip if it's not a nav-link (only intercept nav-link class)
        if (!link.classList.contains('nav-link')) {
            return true;
        }

        return false;
    }

    async navigate(url, link = null) {
        console.log('🔄 AJAX Navigation triggered:', url);
        
        if (this.isNavigating) {
            console.log('⏸️ Navigation already in progress, skipping...');
            return;
        }

        // Don't navigate if already on the same page
        if (url === this.currentUrl) {
            console.log('📍 Already on this page, skipping navigation');
            return;
        }

        this.isNavigating = true;

        try {
            // Update active link immediately for better UX
            if (link) {
                this.updateActiveLink(link);
            }

            // Show skeleton loading immediately
            this.showSkeletonLoading();
            
            // Add a small delay to ensure skeleton is visible
            await new Promise(resolve => setTimeout(resolve, 150));

            // Load the page
            const startTime = Date.now();
            await this.loadPage(url, true);
            
            // Ensure skeleton is visible for at least 1000ms for better UX
            const loadTime = Date.now() - startTime;
            if (loadTime < 1000) {
                await new Promise(resolve => setTimeout(resolve, 1000 - loadTime));
            }

            // Update current URL
            this.currentUrl = url;

            // Update browser history
            if (window.history.pushState) {
                window.history.pushState({ ajax: true, url: url }, '', url);
            }

            // Update page title
            this.updatePageTitle();

            // Trigger custom event
            this.triggerNavigationEvent(url);

            // Preload related pages for faster navigation
            this.preloadRelatedPages(url);

        } catch (error) {
            console.error('Navigation error:', error);
            this.showError('Failed to load page. Please try again.');
            // Fallback to regular page load
            window.location.href = url;
        } finally {
            this.hideSkeletonLoading();
            this.isNavigating = false;
        }
    }

    async loadPage(url, useCache = true) {
        // Check cache first
        if (useCache && this.cache.has(url)) {
            const cachedData = this.cache.get(url);
            this.displayContent(cachedData);
            return cachedData;
        }

        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const html = await response.text();
            console.log('📄 AJAX Response received, length:', html.length);
            console.log('📄 Response preview:', html.substring(0, 500));
            
            // Cache the response
            if (useCache) {
                this.cache.set(url, html);
            // Limit cache size
            if (this.cache.size > 10) {
                const firstKey = this.cache.keys().next().value;
                this.cache.delete(firstKey);
            }
            }

            this.displayContent(html);
            return html;

        } catch (error) {
            console.error('Failed to load page:', error);
            throw error;
        }
    }

    displayContent(html) {
        const mainContent = document.getElementById('main-content');
        if (!mainContent) {
            throw new Error('Main content container not found');
        }

        // Create a temporary container to parse the HTML
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;

        // Extract the main content from the response
        let newContent = tempDiv.querySelector('#main-content');
        
        // If no #main-content found, look for block content
        if (!newContent) {
            console.log('🔍 No #main-content found, searching for alternatives...');
            
            // Check if this is a Django template with block content
            const blockContent = tempDiv.querySelector('[data-block-content]') || 
                                tempDiv.querySelector('.container') ||
                                tempDiv.querySelector('main') ||
                                tempDiv.querySelector('.content') ||
                                tempDiv.querySelector('.page-content');
            
            if (blockContent) {
                console.log('✅ Found content in:', blockContent.tagName, blockContent.className);
                newContent = blockContent;
            } else {
                console.log('⚠️ No suitable content found, using full response');
                // If still no content found, check if the response is a full page
                const bodyContent = tempDiv.querySelector('body');
                if (bodyContent) {
                    // Extract everything inside body
                    newContent = document.createElement('div');
                    newContent.innerHTML = bodyContent.innerHTML;
                } else {
                    newContent = tempDiv;
                }
            }
        } else {
            console.log('✅ Found #main-content');
        }
        
        // Update content first
        mainContent.innerHTML = newContent.innerHTML;
        
        // Reset opacity and add fade-in animation
        mainContent.style.opacity = '0';
        mainContent.style.transform = 'translateY(10px)';
        
        // Hide skeleton loading after a brief delay
        setTimeout(() => {
            this.hideSkeletonLoading();
        }, 100);
        
        requestAnimationFrame(() => {
            mainContent.style.transition = 'opacity 0.4s ease-out, transform 0.4s ease-out';
            mainContent.style.opacity = '1';
            mainContent.style.transform = 'translateY(0)';
        });

        // Reinitialize any page-specific JavaScript
        this.initializePageScripts();
        
        // Special handling for materials/equipment pages
        this.initializeLogisticsPages();
    }

    preloadRelatedPages(currentUrl) {
        // Preload related pages based on current URL
        const relatedUrls = this.getRelatedUrls(currentUrl);
        
        relatedUrls.forEach(url => {
            if (!this.cache.has(url)) {
                // Preload in background
                fetch(url, {
                    method: 'GET',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                    },
                    credentials: 'same-origin'
                })
                .then(response => response.text())
                .then(html => {
                    this.cache.set(url, html);
                })
                .catch(error => {
                    console.warn('Failed to preload:', url, error);
                });
            }
        });
    }

    getRelatedUrls(currentUrl) {
        const relatedUrls = [];
        
        // Define related page patterns
        if (currentUrl.includes('/projects/')) {
            relatedUrls.push('/projects/', '/projects/pending/', '/projects/drafts/');
        } else if (currentUrl.includes('/clients/')) {
            relatedUrls.push('/clients/', '/projects/');
        } else if (currentUrl.includes('/employees/')) {
            relatedUrls.push('/employees/', '/projects/');
        }
        
        return relatedUrls;
    }

    initializePageScripts() {
        // Reinitialize any page-specific JavaScript that might need to run
        const scripts = document.querySelectorAll('#main-content script');
        scripts.forEach(script => {
            if (script.src) {
                // External script - reload
                const newScript = document.createElement('script');
                newScript.src = script.src;
                newScript.async = true;
                document.head.appendChild(newScript);
            } else {
                // Inline script - execute
                try {
                    eval(script.innerHTML);
                } catch (error) {
                    console.warn('Error executing inline script:', error);
                }
            }
        });
    }

    showSkeletonLoading() {
        const mainContent = document.getElementById('main-content');
        if (mainContent && this.skeletonContainer) {
            console.log('🦴 Showing skeleton loading...');
            
            // Clear any existing skeleton
            const existingSkeleton = mainContent.querySelector('#skeleton-loader');
            if (existingSkeleton) {
                existingSkeleton.remove();
            }
            
            // Show skeleton in main content area
            this.skeletonContainer.classList.remove('hidden');
            this.skeletonContainer.style.position = 'absolute';
            this.skeletonContainer.style.top = '0';
            this.skeletonContainer.style.left = '0';
            this.skeletonContainer.style.right = '0';
            this.skeletonContainer.style.bottom = '0';
            this.skeletonContainer.style.padding = '2rem';
            this.skeletonContainer.style.zIndex = '50';
            this.skeletonContainer.style.backgroundColor = '#ffffff';
            this.skeletonContainer.style.overflow = 'auto';
            this.skeletonContainer.style.borderRadius = '0.5rem';
            this.skeletonContainer.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
            
            // Insert skeleton into main content
            mainContent.appendChild(this.skeletonContainer);
            
            // Fade in skeleton
            this.skeletonContainer.style.opacity = '0';
            this.skeletonContainer.style.transform = 'translateY(10px)';
            requestAnimationFrame(() => {
                this.skeletonContainer.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
                this.skeletonContainer.style.opacity = '1';
                this.skeletonContainer.style.transform = 'translateY(0)';
            });
            
            // Add a subtle pulse animation to make it more noticeable
            this.skeletonContainer.style.animation = 'pulse 2s infinite';
        } else {
            console.log('❌ Cannot show skeleton - mainContent or skeletonContainer not found');
        }
    }

    hideSkeletonLoading() {
        if (this.skeletonContainer) {
            console.log('🦴 Hiding skeleton loading...');
            
            // Fade out skeleton
            this.skeletonContainer.style.opacity = '0';
            this.skeletonContainer.style.transition = 'opacity 0.3s ease-out';
            
            setTimeout(() => {
                this.skeletonContainer.classList.add('hidden');
                // Remove from DOM
                if (this.skeletonContainer.parentNode) {
                    this.skeletonContainer.parentNode.removeChild(this.skeletonContainer);
                }
            }, 300);
        }
    }

    initializeActiveStates() {
        // Clear all active states first
        document.querySelectorAll('.nav-link[data-nav-active="true"]').forEach(link => {
            link.removeAttribute('data-nav-active');
            link.classList.remove('active', 'bg-blue-100', 'text-blue-600', 'border-blue-500');
        });

        // Set active state based on current URL
        const currentPath = window.location.pathname;
        let activeLink = null;

        // Find the best matching link
        document.querySelectorAll('.nav-link').forEach(link => {
            const href = link.getAttribute('href');
            if (href === currentPath) {
                activeLink = link;
            } else if (currentPath.startsWith(href) && href !== '/' && href.length > 1) {
                // Check if this is a more specific match
                if (!activeLink || href.length > activeLink.getAttribute('href').length) {
                    activeLink = link;
                }
            }
        });

        // Set active state
        if (activeLink) {
            activeLink.setAttribute('data-nav-active', 'true');
            activeLink.classList.add('active', 'bg-blue-100', 'text-blue-600', 'border-blue-500');
        }
    }

    showError(message) {
        // Create error notification
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg shadow-lg z-50 max-w-sm';
        errorDiv.innerHTML = `
            <div class="flex items-center">
                <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
                </svg>
                <span class="font-medium">${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-red-500 hover:text-red-700">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                    </svg>
                </button>
            </div>
        `;
        
        document.body.appendChild(errorDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (document.body.contains(errorDiv)) {
                errorDiv.style.opacity = '0';
                errorDiv.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (document.body.contains(errorDiv)) {
                        document.body.removeChild(errorDiv);
                    }
                }, 300);
            }
        }, 5000);
    }

    updatePageContent(content, title) {
        // Find the main content container
        const mainContent = document.querySelector('#main-content') || 
                           document.querySelector('main') || 
                           document.querySelector('.content') ||
                           document.querySelector('.container');

        if (mainContent) {
            // Add fade out effect
            mainContent.style.opacity = '0';
            mainContent.style.transition = 'opacity 0.3s ease-in-out';

            setTimeout(() => {
                mainContent.innerHTML = content;
                mainContent.style.opacity = '1';

                // Re-initialize any components that need it
                this.reinitializeComponents();
            }, 150);
        } else {
            // Fallback: update body content
            document.body.innerHTML = content;
            this.reinitializeComponents();
        }
    }

    updatePageTitle(title) {
        if (title && title !== document.title) {
            document.title = title;
        }
    }

    updateActiveLink(activeLink) {
        // Remove active class from all navigation links
        document.querySelectorAll('.nav-link, .sidebar-link, [data-nav-active]').forEach(link => {
            link.classList.remove('active', 'bg-blue-100', 'text-blue-600', 'border-blue-500');
            link.removeAttribute('data-nav-active');
            // Reset any active styling
            link.style.backgroundColor = '';
            link.style.borderLeft = '';
        });

        // Add active class to current link
        if (activeLink) {
        activeLink.classList.add('active', 'bg-blue-100', 'text-blue-600', 'border-blue-500');
            activeLink.setAttribute('data-nav-active', 'true');
        }
    }

    reinitializeComponents() {
        // Re-initialize any JavaScript components that need it
        this.initializeTooltips();
        this.initializeModals();
        this.initializeForms();
        this.initializeDataTables();
        
        // Trigger custom event for other components to reinitialize
        document.dispatchEvent(new CustomEvent('ajaxContentLoaded', {
            detail: { url: this.currentUrl }
        }));
    }

    initializeTooltips() {
        // Re-initialize tooltips if using a tooltip library
        if (typeof tippy !== 'undefined') {
            tippy('[data-tippy-content]');
        }
    }

    initializeModals() {
        // Re-initialize modals
        document.querySelectorAll('[data-modal]').forEach(modal => {
            modal.addEventListener('click', (e) => {
                e.preventDefault();
                const modalId = modal.getAttribute('data-modal');
                const modalElement = document.getElementById(modalId);
                if (modalElement) {
                    modalElement.classList.remove('hidden');
                }
            });
        });
    }

    initializeForms() {
        // Re-initialize form enhancements
        document.querySelectorAll('form').forEach(form => {
            if (!form.hasAttribute('data-initialized')) {
                form.setAttribute('data-initialized', 'true');
                // Add any form-specific initialization here
            }
        });
    }

    initializeDataTables() {
        // Re-initialize data tables if using DataTables
        if (typeof $.fn.DataTable !== 'undefined') {
            $('.data-table').DataTable();
        }
    }

    async submitForm(form) {
        const formData = new FormData(form);
        const url = form.action || window.location.pathname;
        const method = form.method || 'POST';

        this.showLoading();

        try {
            const response = await fetch(url, {
                method: method,
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (response.ok) {
                const result = await response.json();
                
                if (result.success) {
                    this.showSuccess(result.message || 'Operation completed successfully');
                    
                    // Redirect if specified
                    if (result.redirect) {
                        setTimeout(() => {
                            this.navigate(result.redirect);
                        }, 1000);
                    }
                } else {
                    this.showError(result.error || 'Operation failed');
                }
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Form submission error:', error);
            this.showError('Failed to submit form. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    setupHistoryAPI() {
        // Ensure we can handle browser back/forward
        if (!window.history.pushState) {
            console.warn('History API not supported, falling back to regular navigation');
        }
    }

    showLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.classList.remove('hidden');
        }
    }

    hideLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.classList.add('hidden');
        }
    }

    showSuccess(message) {
        this.showToast(message, 'success');
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 z-50 px-6 py-3 rounded-lg shadow-lg text-white ${
            type === 'success' ? 'bg-green-500' : 
            type === 'error' ? 'bg-red-500' : 
            'bg-blue-500'
        }`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    triggerNavigationEvent(url) {
        // Trigger custom event for other components
        document.dispatchEvent(new CustomEvent('ajaxNavigation', {
            detail: { url: url, timestamp: Date.now() }
        }));
    }

    // Public methods for external use
    goTo(url) {
        this.navigate(url);
    }

    refresh() {
        this.loadPage(this.currentUrl, false);
    }

    clearCache() {
        this.cache.clear();
    }

    stopDashboardAutoRefresh() {
        // Stop any running dashboard auto-refresh intervals
        if (window.OUR_REFRESH_INTERVAL) {
            clearInterval(window.OUR_REFRESH_INTERVAL);
            window.OUR_REFRESH_INTERVAL = null;
            console.log('🛑 Stopped dashboard auto-refresh');
        }
        
        // Stop dashboard auto-refresh class if it exists
        if (window.DashboardAutoRefresh && window.DashboardAutoRefresh.stopAutoRefresh) {
            window.DashboardAutoRefresh.stopAutoRefresh();
            console.log('🛑 Stopped DashboardAutoRefresh class');
        }
        
        // Clear any other potential intervals
        for (let i = 1; i < 99999; i++) {
            clearInterval(i);
        }
    }

    initializeLogisticsPages() {
        // Check if we're on a logistics page and initialize data loading
        const currentUrl = window.location.pathname;
        
        if (currentUrl.includes('/materials/') || currentUrl.includes('/equipment/')) {
            console.log('🚚 Initializing logistics page:', currentUrl);
            
            // Initialize materials page
            if (currentUrl.includes('/materials/')) {
                this.initializeMaterialsPage();
            }
            
            // Initialize equipment page
            if (currentUrl.includes('/equipment/')) {
                this.initializeEquipmentPage();
            }
        }
    }

    initializeMaterialsPage() {
        console.log('📦 Initializing materials page...');
        
        // Load materials data
        if (typeof loadMaterials === 'function') {
            loadMaterials();
        } else {
            // Fallback: make direct API call
            this.loadMaterialsData();
        }
        
        // Load stats
        if (typeof loadStats === 'function') {
            loadStats();
        } else {
            this.loadMaterialsStats();
        }
        
        // Load categories
        if (typeof loadCategories === 'function') {
            loadCategories();
        }
    }

    initializeEquipmentPage() {
        console.log('🔧 Initializing equipment page...');
        
        // Load equipment data
        if (typeof loadEquipment === 'function') {
            loadEquipment();
        } else {
            // Fallback: make direct API call
            this.loadEquipmentData();
        }
    }

    async loadMaterialsData() {
        try {
            const response = await fetch('/materials/api/materials/');
            const data = await response.json();
            
            if (data.materials) {
                this.renderMaterialsTable(data.materials);
            }
        } catch (error) {
            console.error('Error loading materials:', error);
        }
    }

    async loadMaterialsStats() {
        try {
            // This would need to be implemented based on your stats API
            console.log('Loading materials stats...');
        } catch (error) {
            console.error('Error loading materials stats:', error);
        }
    }

    async loadEquipmentData() {
        try {
            const response = await fetch('/materials/api/equipment/');
            const data = await response.json();
            
            if (data.equipment) {
                this.renderEquipmentTable(data.equipment);
            }
        } catch (error) {
            console.error('Error loading equipment:', error);
        }
    }

    renderMaterialsTable(materials) {
        const tableBody = document.querySelector('#materialsTable tbody');
        if (!tableBody) return;
        
        tableBody.innerHTML = materials.map(material => `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${material.name}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${material.category || 'N/A'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">₱${material.standard_price}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">₱${material.latest_price}</td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button onclick="editMaterial(${material.id}, '${material.name}')" class="text-indigo-600 hover:text-indigo-900">Edit</button>
                    <button onclick="deleteMaterial(${material.id}, '${material.name}')" class="text-red-600 hover:text-red-900 ml-4">Delete</button>
                </td>
            </tr>
        `).join('');
    }

    renderEquipmentTable(equipment) {
        const tableBody = document.querySelector('#equipmentTable tbody');
        if (!tableBody) return;
        
        tableBody.innerHTML = equipment.map(item => `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${item.name}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${item.ownership_type}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${item.rental_rate ? '₱' + item.rental_rate : 'N/A'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${item.purchase_price ? '₱' + item.purchase_price : 'N/A'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button onclick="editEquipment(${item.id}, '${item.name}')" class="text-indigo-600 hover:text-indigo-900">Edit</button>
                    <button onclick="deleteEquipment(${item.id}, '${item.name}')" class="text-red-600 hover:text-red-900 ml-4">Delete</button>
                </td>
            </tr>
        `).join('');
    }
}

// Initialize AJAX navigation when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.ajaxNavigation = new AjaxNavigation();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AjaxNavigation;
}
