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
        console.log('✅ AJAX Navigation fully initialized');
    }

    createSkeletonLoader() {
        // Create skeleton loading container
        this.skeletonContainer = document.createElement('div');
        this.skeletonContainer.id = 'skeleton-loader';
        this.skeletonContainer.className = 'hidden';
        this.skeletonContainer.innerHTML = `
            <div class="animate-pulse space-y-6 p-4">
                <!-- Header skeleton -->
                <div class="space-y-3">
                    <div class="h-8 bg-gray-300 rounded-lg w-1/3"></div>
                    <div class="h-4 bg-gray-300 rounded w-1/2"></div>
                </div>
                
                <!-- Stats cards skeleton -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                    <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                        <div class="flex items-center justify-between mb-4">
                            <div class="w-12 h-12 bg-gray-300 rounded-2xl"></div>
                            <div class="text-right">
                                <div class="h-8 bg-gray-300 rounded w-16 mb-2"></div>
                                <div class="h-3 bg-gray-300 rounded w-12"></div>
                            </div>
                        </div>
                        <div class="h-6 bg-gray-300 rounded w-3/4 mb-2"></div>
                        <div class="h-4 bg-gray-300 rounded w-1/2"></div>
                    </div>
                    <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                        <div class="flex items-center justify-between mb-4">
                            <div class="w-12 h-12 bg-gray-300 rounded-2xl"></div>
                            <div class="text-right">
                                <div class="h-8 bg-gray-300 rounded w-16 mb-2"></div>
                                <div class="h-3 bg-gray-300 rounded w-12"></div>
                            </div>
                        </div>
                        <div class="h-6 bg-gray-300 rounded w-3/4 mb-2"></div>
                        <div class="h-4 bg-gray-300 rounded w-1/2"></div>
                    </div>
                    <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                        <div class="flex items-center justify-between mb-4">
                            <div class="w-12 h-12 bg-gray-300 rounded-2xl"></div>
                            <div class="text-right">
                                <div class="h-8 bg-gray-300 rounded w-16 mb-2"></div>
                                <div class="h-3 bg-gray-300 rounded w-12"></div>
                            </div>
                        </div>
                        <div class="h-6 bg-gray-300 rounded w-3/4 mb-2"></div>
                        <div class="h-4 bg-gray-300 rounded w-1/2"></div>
                    </div>
                    <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                        <div class="flex items-center justify-between mb-4">
                            <div class="w-12 h-12 bg-gray-300 rounded-2xl"></div>
                            <div class="text-right">
                                <div class="h-8 bg-gray-300 rounded w-16 mb-2"></div>
                                <div class="h-3 bg-gray-300 rounded w-12"></div>
                            </div>
                        </div>
                        <div class="h-6 bg-gray-300 rounded w-3/4 mb-2"></div>
                        <div class="h-4 bg-gray-300 rounded w-1/2"></div>
                    </div>
                </div>
                
                <!-- Table skeleton -->
                <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                    <div class="p-6 border-b border-gray-200">
                        <div class="h-6 bg-gray-300 rounded w-1/4"></div>
                    </div>
                    <div class="p-6 space-y-4">
                        <div class="flex space-x-4">
                            <div class="h-4 bg-gray-300 rounded flex-1"></div>
                            <div class="h-4 bg-gray-300 rounded w-24"></div>
                            <div class="h-4 bg-gray-300 rounded w-20"></div>
                            <div class="h-4 bg-gray-300 rounded w-16"></div>
                        </div>
                        <div class="flex space-x-4">
                            <div class="h-4 bg-gray-200 rounded flex-1"></div>
                            <div class="h-4 bg-gray-200 rounded w-24"></div>
                            <div class="h-4 bg-gray-200 rounded w-20"></div>
                            <div class="h-4 bg-gray-200 rounded w-16"></div>
                        </div>
                        <div class="flex space-x-4">
                            <div class="h-4 bg-gray-200 rounded flex-1"></div>
                            <div class="h-4 bg-gray-200 rounded w-24"></div>
                            <div class="h-4 bg-gray-200 rounded w-20"></div>
                            <div class="h-4 bg-gray-200 rounded w-16"></div>
                        </div>
                        <div class="flex space-x-4">
                            <div class="h-4 bg-gray-200 rounded flex-1"></div>
                            <div class="h-4 bg-gray-200 rounded w-24"></div>
                            <div class="h-4 bg-gray-200 rounded w-20"></div>
                            <div class="h-4 bg-gray-200 rounded w-16"></div>
                        </div>
                        <div class="flex space-x-4">
                            <div class="h-4 bg-gray-200 rounded flex-1"></div>
                            <div class="h-4 bg-gray-200 rounded w-24"></div>
                            <div class="h-4 bg-gray-200 rounded w-20"></div>
                            <div class="h-4 bg-gray-200 rounded w-16"></div>
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
            console.log('🔗 Link clicked:', href);
            
            // Skip if it's an external link, mailto, tel, or has special attributes
            if (this.shouldSkipLink(link, href)) {
                console.log('🚫 Link skipped:', href);
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
            console.log('🚀 Starting AJAX navigation to:', href);
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
            console.log('🚫 Skipping link with data-skip-ajax:', href);
            return true;
        }

        // Skip if it's a hash link
        if (href.startsWith('#')) {
            return true;
        }

        // Skip empty href or root path that should redirect to dashboard
        if (href === '' || href === '/') {
            // Use AJAX navigation for dashboard redirects
            this.navigate('/dashboard/', link);
            return true;
        }

        return false;
    }

    async navigate(url, link = null) {
        console.log('🔄 AJAX Navigation triggered:', url);
        
        // Special debug for logistics URLs
        if (url.includes('/materials/') || url.includes('/equipment/') || url.includes('/price-monitoring/')) {
            console.log('🚛 Logistics navigation detected:', url);
            console.log('🔗 Link element:', link);
            console.log('📱 Has skip-ajax attribute:', link?.getAttribute('data-skip-ajax'));
        }
        
        if (this.isNavigating) {
            console.log('⏸️ Navigation already in progress, skipping...');
            return;
        }

        // Don't navigate if already on the same page
        if (url === this.currentUrl) {
            console.log('📍 Already on this page, skipping navigation');
            return;
        }

        // Dashboard navigation now uses AJAX for seamless experience
        if (url.includes('/dashboard/') || url === '/dashboard/') {
            console.log('🏠 Dashboard navigation detected - using AJAX for:', url);
        }

        this.isNavigating = true;

        try {
            // Update active link immediately for better UX
            if (link) {
                this.updateActiveLink(link);
            }

            // Show skeleton loading immediately
            this.showSkeletonLoading();

            // Load the page
            await this.loadPage(url, true);

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
            console.error('URL that failed:', url);
            this.showError('Failed to load page. Please try again.');
            // Fallback to regular page load
            console.log('🔄 Falling back to regular page load for:', url);
            window.location.href = url;
        } finally {
            this.hideSkeletonLoading();
            this.isNavigating = false;
        }
    }

    async loadPage(url, useCache = true) {
        console.log('📥 Loading page:', url);
        
        // Check cache first
        if (useCache && this.cache.has(url)) {
            console.log('💾 Using cached data for:', url);
            const cachedData = this.cache.get(url);
            this.displayContent(cachedData);
            return cachedData;
        }

        try {
            console.log('🌐 Making AJAX request to:', url);
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                },
                credentials: 'same-origin'
            });
            
            console.log('📡 Response received:', response.status, response.statusText);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // Check if the response is a redirect
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const jsonResponse = await response.json();
                if (jsonResponse.redirect) {
                    console.log('🔄 Redirect response received:', jsonResponse.redirect);
                    // Handle redirect by doing a full page reload
                    window.location.href = jsonResponse.redirect;
                    return;
                }
            }

            const html = await response.text();
            
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
        console.log('🔄 AJAX Navigation: Displaying content...');
        
        const mainContent = document.getElementById('main-content');
        if (!mainContent) {
            throw new Error('Main content container not found');
        }

        // Create a temporary container to parse the HTML
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;

        // Debug: Log what we found in the response
        console.log('📄 Response HTML length:', html.length);
        console.log('📄 Response preview:', html.substring(0, 200) + '...');
        console.log('📄 Found elements:', {
            mainContent: !!tempDiv.querySelector('#main-content'),
            main: !!tempDiv.querySelector('main'),
            contentArea: !!tempDiv.querySelector('.content-area'),
            container: !!tempDiv.querySelector('.container'),
            body: !!tempDiv.querySelector('body'),
            logisticsContent: !!tempDiv.querySelector('.space-y-6')
        });

        // Extract the main content from the response
        // Look for main-content first, then main, then content area, then fallback to body content
        let newContent = tempDiv.querySelector('#main-content');
        if (!newContent) {
            newContent = tempDiv.querySelector('main');
        }
        if (!newContent) {
            newContent = tempDiv.querySelector('.content-area');
        }
        if (!newContent) {
            newContent = tempDiv.querySelector('.container');
        }
        if (!newContent) {
            // If no specific container found, look for the content block
            newContent = tempDiv.querySelector('[class*="content"]') || tempDiv.querySelector('body') || tempDiv;
        }
        
        console.log('📦 Selected content element:', newContent?.tagName, newContent?.className);
        console.log('📦 Content length:', newContent?.innerHTML?.length || 0);
        
        // Hide skeleton loading first
        this.hideSkeletonLoading();
        
        // Update content
        if (newContent && newContent.innerHTML) {
            mainContent.innerHTML = newContent.innerHTML;
            console.log('✅ Content updated successfully');
        } else {
            // Fallback: use the entire response
            mainContent.innerHTML = html;
            console.log('⚠️ Using fallback content');
        }
        
        // Reset opacity and add fade-in animation
        mainContent.style.opacity = '0';
        mainContent.style.transform = 'translateY(10px)';
        
        requestAnimationFrame(() => {
            mainContent.style.transition = 'opacity 0.4s ease-out, transform 0.4s ease-out';
            mainContent.style.opacity = '1';
            mainContent.style.transform = 'translateY(0)';
        });

        // Initialize page-specific scripts first
        this.initializePageSpecificScripts();
        
        // Then initialize general page scripts
        this.initializePageScripts();
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
        } else if (currentUrl.includes('/manage-client/clients/')) {
            relatedUrls.push('/manage-client/clients/', '/projects/');
        } else if (currentUrl.includes('/employees/')) {
            relatedUrls.push('/employees/', '/projects/');
        }
        
        return relatedUrls;
    }

    initializePageScripts() {
        console.log('🔧 AJAX Navigation: Initializing page scripts...');
        
        // Wait for DOM to be ready
        setTimeout(() => {
            // Reinitialize any page-specific JavaScript that might need to run
            const scripts = document.querySelectorAll('#main-content script');
            console.log('📜 Found', scripts.length, 'scripts in new content');
            
            scripts.forEach((script, index) => {
                console.log(`📜 Script ${index + 1}:`, script.src || 'inline script');
                
                if (script.src) {
                    // External script - reload
                    console.log('📜 Loading external script:', script.src);
                    const newScript = document.createElement('script');
                    newScript.src = script.src;
                    newScript.async = true;
                    document.head.appendChild(newScript);
                } else {
                    // Inline script - execute in global scope
                    try {
                        console.log('📜 Executing inline script');
                        // Execute script content directly in global scope
                        eval(script.innerHTML);
                    } catch (error) {
                        console.warn('❌ Error executing inline script:', error);
                    }
                }
            });
            
            // Setup event delegation for common patterns
            this.setupEventDelegation();
            
            // Initialize page-specific functionality
            this.initializePageSpecificScripts();
            
            // Initialize current module
            this.initializeCurrentModule();
            
            // Trigger custom event for other components to reinitialize
            console.log('📡 Triggering ajaxContentLoaded event...');
            document.dispatchEvent(new CustomEvent('ajaxContentLoaded', {
                detail: { url: this.currentUrl }
            }));
            
            console.log('✅ AJAX Navigation: Page scripts initialized');
        }, 100);
    }

    setupEventDelegation() {
        console.log('🔧 AJAX Navigation: Setting up event delegation...');
        
        // Remove existing delegation listeners to prevent duplicates
        if (this.delegationController) {
            this.delegationController.abort();
        }
        this.delegationController = new AbortController();
        
        // Modal handling delegation
        document.addEventListener('click', (e) => {
            const modalTrigger = e.target.closest('[data-modal-trigger]');
            if (modalTrigger) {
                e.preventDefault();
                const modalId = modalTrigger.dataset.modalId;
                if (modalId) {
                    const modal = document.getElementById(modalId);
                    if (modal) {
                        modal.classList.remove('hidden');
                        console.log('📱 Modal opened via delegation:', modalId);
                    }
                }
            }
            
            const modalClose = e.target.closest('[data-modal-close]');
            if (modalClose) {
                e.preventDefault();
                const modalId = modalClose.dataset.modalId;
                if (modalId) {
                    const modal = document.getElementById(modalId);
                    if (modal) {
                        modal.classList.add('hidden');
                        console.log('📱 Modal closed via delegation:', modalId);
                    }
                }
            }
        }, { signal: this.delegationController.signal });
        
        // Form submission delegation
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.hasAttribute('data-ajax-form')) {
                e.preventDefault();
                this.submitForm(form);
            }
        }, { signal: this.delegationController.signal });
        
        console.log('✅ Event delegation setup complete');
    }

    initializeCurrentModule() {
        console.log('🔧 AJAX Navigation: Initializing current module...');
        
        // Use module registry if available
        if (window.ModuleRegistry) {
            const path = window.location.pathname;
            for (let pattern in window.ModuleRegistry) {
                if (path.includes(pattern)) {
                    console.log(`🏗️ Initializing module for pattern: ${pattern}`);
                    try {
                        window.ModuleRegistry[pattern]();
                    } catch (error) {
                        console.error(`❌ Error initializing module ${pattern}:`, error);
                    }
                }
            }
        } else {
            // Fallback to specific module detection
            this.initializePageSpecificScripts();
        }
    }

    initializePageSpecificScripts() {
        console.log('🔧 AJAX Navigation: Initializing page-specific scripts...');
        
        // Handle dashboard
        if (this.currentUrl.includes('/dashboard/')) {
            console.log('🏠 Initializing dashboard...');
            if (typeof window.initializeDashboard === 'function') {
                setTimeout(() => {
                    window.initializeDashboard();
                }, 200);
            }
        }
        
        // Handle client management
        if (this.currentUrl.includes('/manage-client/')) {
            console.log('👥 Initializing client management...');
            if (typeof window.initializeClientManagement === 'function') {
                setTimeout(() => {
                    window.initializeClientManagement();
                }, 200);
            }
        }
        
        // Handle price monitoring page
        if (this.currentUrl.includes('/price-monitoring/')) {
            console.log('💰 Initializing price monitoring page...');
            if (typeof window.initializePriceMonitoring === 'function') {
                setTimeout(() => {
                    window.initializePriceMonitoring();
                }, 200);
            }
        }
        
        // Handle materials page
        if (this.currentUrl.includes('/materials/') && !this.currentUrl.includes('/price-monitoring/')) {
            console.log('📦 Initializing materials page...');
            if (typeof window.loadMaterials === 'function') {
                setTimeout(() => {
                    window.loadMaterials();
                    if (typeof window.loadCategories === 'function') {
                        window.loadCategories();
                    }
                }, 200);
            }
        }
        
        // Handle equipment page
        if (this.currentUrl.includes('/equipment/')) {
            console.log('🔧 Initializing equipment page...');
            if (typeof window.loadEquipment === 'function') {
                setTimeout(() => {
                    window.loadEquipment();
                }, 200);
            }
        }
        
        // Handle projects
        if (this.currentUrl.includes('/projects/')) {
            console.log('📋 Initializing projects...');
            if (typeof window.initializeProjects === 'function') {
                setTimeout(() => {
                    window.initializeProjects();
                }, 200);
            }
        }
        
        // Handle employees
        if (this.currentUrl.includes('/employees/')) {
            console.log('👷 Initializing employees...');
            if (typeof window.initializeEmployees === 'function') {
                setTimeout(() => {
                    window.initializeEmployees();
                }, 200);
            }
        }
    }

    showSkeletonLoading() {
        console.log('⏳ AJAX Navigation: Showing skeleton loading...');
        
        const mainContent = document.getElementById('main-content');
        if (mainContent && this.skeletonContainer) {
            // Hide current content with fade effect
            mainContent.style.transition = 'opacity 0.3s ease-out';
            mainContent.style.opacity = '0.3';
            
            // Show skeleton in main content area
            this.skeletonContainer.classList.remove('hidden');
            this.skeletonContainer.style.position = 'absolute';
            this.skeletonContainer.style.top = '0';
            this.skeletonContainer.style.left = '0';
            this.skeletonContainer.style.right = '0';
            this.skeletonContainer.style.padding = '1.5rem';
            this.skeletonContainer.style.zIndex = '10';
            this.skeletonContainer.style.backgroundColor = 'rgba(249, 250, 251, 0.9)';
            this.skeletonContainer.style.backdropFilter = 'blur(2px)';
            
            // Insert skeleton into main content
            mainContent.appendChild(this.skeletonContainer);
            
            console.log('✅ Skeleton loading displayed');
        }
    }

    hideSkeletonLoading() {
        console.log('✅ AJAX Navigation: Hiding skeleton loading...');
        
        if (this.skeletonContainer) {
            this.skeletonContainer.classList.add('hidden');
            // Remove from DOM
            if (this.skeletonContainer.parentNode) {
                this.skeletonContainer.parentNode.removeChild(this.skeletonContainer);
            }
        }
        
        // Restore main content opacity
        const mainContent = document.getElementById('main-content');
        if (mainContent) {
            mainContent.style.opacity = '1';
        }
        
        console.log('✅ Skeleton loading hidden');
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
}

// Initialize AJAX navigation when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 DOM Content Loaded - Checking AJAX Navigation...');
    try {
        window.ajaxNavigation = new AjaxNavigation();
        console.log('✅ AJAX Navigation is ready and initialized');
    } catch (error) {
        console.error('❌ AJAX Navigation initialization failed:', error);
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AjaxNavigation;
}


