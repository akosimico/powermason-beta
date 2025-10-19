/**
 * Skeleton Loader Utility
 * Provides functions for showing/hiding skeleton screens
 */

const SkeletonLoader = {
    /**
     * Show skeleton in a container
     * @param {string} containerId - ID of container element
     * @param {string} skeletonType - Type of skeleton to show
     */
    show(containerId, skeletonType = 'card') {
        const container = document.getElementById(containerId);
        if (!container) return;

        const skeleton = this.getSkeletonHTML(skeletonType);
        container.innerHTML = skeleton;
        container.classList.add('skeleton-container');
    },

    /**
     * Hide skeleton and show content
     * @param {string} containerId - ID of container element
     * @param {string} content - HTML content to display
     */
    hide(containerId, content) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = content;
        container.classList.remove('skeleton-container');
        container.classList.add('skeleton-loaded');
    },

    /**
     * Get skeleton HTML based on type
     * @param {string} type - Skeleton type
     * @returns {string} HTML string
     */
    getSkeletonHTML(type) {
        const skeletons = {
            'stat-card': `
                <div class="skeleton-stat-card">
                    <div class="skeleton skeleton-stat-icon"></div>
                    <div class="skeleton skeleton-stat-number"></div>
                    <div class="skeleton skeleton-stat-label"></div>
                </div>
            `,
            'project-item': `
                <div class="skeleton-project-item">
                    <div class="skeleton skeleton-avatar large"></div>
                    <div class="skeleton-project-content">
                        <div class="skeleton skeleton-title"></div>
                        <div class="skeleton skeleton-text medium"></div>
                        <div class="skeleton-project-meta">
                            <div class="skeleton skeleton-badge"></div>
                            <div class="skeleton skeleton-badge"></div>
                        </div>
                    </div>
                </div>
            `,
            'budget-row': `
                <div class="skeleton-budget-row">
                    <div class="skeleton skeleton-text"></div>
                    <div class="skeleton skeleton-text short"></div>
                    <div class="skeleton skeleton-text short"></div>
                    <div class="skeleton skeleton-progress-bar"></div>
                    <div class="skeleton skeleton-badge"></div>
                </div>
            `,
            'chart': '<div class="skeleton skeleton-chart"></div>',
            'map': '<div class="skeleton skeleton-map"></div>',
            'table': this.getTableSkeleton(5),
            'card': `
                <div class="skeleton-card">
                    <div class="skeleton skeleton-title"></div>
                    <div class="skeleton skeleton-text"></div>
                    <div class="skeleton skeleton-text medium"></div>
                    <div class="skeleton skeleton-text short"></div>
                </div>
            `
        };

        return skeletons[type] || skeletons['card'];
    },

    /**
     * Generate table skeleton with specified rows
     * @param {number} rows - Number of rows
     * @returns {string} HTML string
     */
    getTableSkeleton(rows = 5) {
        let html = '<div class="skeleton-container">';
        for (let i = 0; i < rows; i++) {
            html += `
                <div class="skeleton-table-row">
                    <div class="skeleton skeleton-table-cell"></div>
                    <div class="skeleton skeleton-table-cell"></div>
                    <div class="skeleton skeleton-table-cell"></div>
                    <div class="skeleton skeleton-table-cell"></div>
                </div>
            `;
        }
        html += '</div>';
        return html;
    },

    /**
     * Show multiple skeletons in a grid
     * @param {string} containerId - Container ID
     * @param {string} skeletonType - Type of skeleton
     * @param {number} count - Number of skeletons
     * @param {string} gridClass - CSS class for grid layout
     */
    showGrid(containerId, skeletonType, count, gridClass = 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6') {
        const container = document.getElementById(containerId);
        if (!container) return;

        const skeleton = this.getSkeletonHTML(skeletonType);
        let html = `<div class="${gridClass}">`;
        for (let i = 0; i < count; i++) {
            html += skeleton;
        }
        html += '</div>';

        container.innerHTML = html;
        container.classList.add('skeleton-container');
    },

    /**
     * Show skeleton with custom HTML
     * @param {string} containerId - Container ID
     * @param {string} customHTML - Custom skeleton HTML
     */
    showCustom(containerId, customHTML) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = customHTML;
        container.classList.add('skeleton-container');
    },

    /**
     * Replace skeleton with loaded content smoothly
     * @param {string} containerId - Container ID
     * @param {Function} loadFunction - Async function that returns content
     */
    async loadWithSkeleton(containerId, skeletonType, loadFunction) {
        // Show skeleton
        this.show(containerId, skeletonType);

        try {
            // Load content
            const content = await loadFunction();

            // Hide skeleton and show content
            this.hide(containerId, content);
        } catch (error) {
            console.error('Error loading content:', error);
            this.hide(containerId, `
                <div class="text-center text-red-600 py-4">
                    <p>Error loading content. Please refresh the page.</p>
                </div>
            `);
        }
    },

    /**
     * Progressive load multiple sections
     * @param {Array} sections - Array of {containerId, skeletonType, loadFunction}
     */
    async progressiveLoad(sections) {
        // Show all skeletons first
        sections.forEach(section => {
            this.show(section.containerId, section.skeletonType);
        });

        // Load sections in sequence
        for (const section of sections) {
            try {
                const content = await section.loadFunction();
                this.hide(section.containerId, content);

                // Small delay for smoother UX
                await new Promise(resolve => setTimeout(resolve, 100));
            } catch (error) {
                console.error(`Error loading ${section.containerId}:`, error);
                this.hide(section.containerId, `
                    <div class="text-center text-red-600 py-4">
                        <p>Error loading this section.</p>
                    </div>
                `);
            }
        }
    }
};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SkeletonLoader;
}
