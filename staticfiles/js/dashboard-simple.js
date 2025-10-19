// Simple Dashboard Manual Updates Only
// Clean, lightweight system without auto-refresh

class SimpleDashboard {
    constructor() {
        this.isUpdating = false;
        this.init();
    }

    init() {
        console.log('🚀 Simple Dashboard initialized (Manual updates only)');
        
        // Add manual refresh button functionality
        this.setupManualRefresh();
    }

    async updateDashboard() {
        if (this.isUpdating) {
            console.log('⏸️ Update already in progress, skipping...');
            return;
        }

        this.isUpdating = true;
        
        try {
            console.log('🔄 Updating dashboard data...');
            
            // Show subtle update indicator
            this.showUpdateIndicator();
            
            // Fetch fresh data from the API
            const response = await fetch('/api/dashboard/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin',
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            if (data.success) {
                this.updateDashboardUI(data);
                this.showUpdateSuccess();
                console.log('✅ Dashboard updated successfully');
            } else {
                throw new Error(data.message || 'Unknown error');
            }

        } catch (error) {
            console.error('❌ Dashboard update failed:', error);
            this.showUpdateError();
        } finally {
            this.isUpdating = false;
        }
    }

    updateDashboardUI(data) {
        // Update metrics
        if (data.metrics) {
            this.updateMetrics(data.metrics);
        }

        // Update project status counts
        if (data.status_counts) {
            this.updateProjectStatus(data.status_counts);
        }

        // Update task status counts
        if (data.task_status_counts) {
            this.updateTaskStatus(data.task_status_counts);
        }

        // Update recent tasks
        if (data.recent_tasks) {
            this.updateRecentTasks(data.recent_tasks);
        }

        // Update projects list
        if (data.projects) {
            this.updateProjectsList(data.projects);
        }
    }

    updateMetrics(metrics) {
        const elements = {
            totalProjects: document.querySelector('[data-metric="total_projects"]'),
            avgProgress: document.querySelector('[data-metric="avg_progress"]'),
            totalBudget: document.querySelector('[data-metric="total_budget_planned"]'),
            budgetUtilization: document.querySelector('[data-metric="budget_utilization"]'),
            taskCompletion: document.querySelector('[data-metric="task_completion_rate"]'),
            overdueTasks: document.querySelector('[data-metric="overdue_tasks"]')
        };
        
        if (elements.totalProjects) elements.totalProjects.textContent = metrics.total_projects || 0;
        if (elements.avgProgress) elements.avgProgress.textContent = (metrics.avg_progress || 0) + '%';
        if (elements.totalBudget) elements.totalBudget.textContent = '₱' + (metrics.total_budget_planned || 0).toLocaleString();
        if (elements.budgetUtilization) elements.budgetUtilization.textContent = (metrics.budget_utilization || 0) + '%';
        if (elements.taskCompletion) elements.taskCompletion.textContent = (metrics.task_completion_rate || 0) + '%';
        if (elements.overdueTasks) elements.overdueTasks.textContent = metrics.overdue_tasks || 0;
        
        console.log('📈 Metrics updated');
    }

    updateProjectStatus(statusCounts) {
        console.log('📋 Project status updated:', statusCounts);
        // Add your project status update logic here
    }

    updateTaskStatus(taskStatusCounts) {
        console.log('✅ Task status updated:', taskStatusCounts);
        // Add your task status update logic here
    }

    updateRecentTasks(recentTasks) {
        console.log('🕒 Recent tasks updated:', recentTasks);
        // Add your recent tasks update logic here
    }

    updateProjectsList(projects) {
        console.log('📊 Projects list updated:', projects.length, 'projects');
        // Add your projects list update logic here
    }

    showUpdateIndicator() {
        // Show subtle loading indicator
        const indicator = document.getElementById('dashboard-update-indicator');
        if (indicator) {
            indicator.style.opacity = '1';
            indicator.textContent = 'Updating...';
        }
    }

    showUpdateSuccess() {
        const indicator = document.getElementById('dashboard-update-indicator');
        if (indicator) {
            indicator.textContent = 'Updated';
            indicator.style.color = '#10b981';
            
            setTimeout(() => {
                indicator.style.opacity = '0';
            }, 2000);
        }
    }

    showUpdateError() {
        const indicator = document.getElementById('dashboard-update-indicator');
        if (indicator) {
            indicator.textContent = 'Update failed';
            indicator.style.color = '#ef4444';
            
            setTimeout(() => {
                indicator.style.opacity = '0';
            }, 3000);
        }
    }

    setupManualRefresh() {
        // Add manual refresh button functionality
        const refreshBtn = document.getElementById('dashboard-refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.updateDashboard();
            });
        }
    }

    // Public method to manually refresh
    refresh() {
        this.updateDashboard();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.simpleDashboard = new SimpleDashboard();
});

// Export for manual use
window.SimpleDashboard = SimpleDashboard;
