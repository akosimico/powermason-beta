document.addEventListener("DOMContentLoaded", function () {
    const toggle = document.getElementById("notifToggle");
    const dropdown = document.getElementById("notifDropdown");
    const markAllBtn = document.getElementById("markAllReadBtn");
    const clearAllBtn = document.getElementById("clearAllBtn");
    const notificationContent = document.getElementById("notificationContent");

    // --- Helper: get CSRF token from cookie ---
    function getCSRFToken() {
        const cookieValue = document.cookie.split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue;
    }

    // --- Load notifications ---
    async function loadNotifications() {
        try {
            const response = await fetch('/notifications/dropdown/');
            if (response.ok) {
                const html = await response.text();
                notificationContent.innerHTML = html;
                
                // Update badge based on content
                updateNotificationBadge();
            } else {
                console.error('Failed to load notifications');
                notificationContent.innerHTML = `
                    <div class="text-center py-8 text-gray-500">
                        <p>Failed to load notifications</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
            notificationContent.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <p>Error loading notifications</p>
                </div>
            `;
        }
    }

    // --- Update notification badge ---
    function updateNotificationBadge() {
        // Count unread notifications (those with blue background)
        const unreadCount = dropdown.querySelectorAll('.bg-blue-50').length;
        
        // Remove existing badge
        const existingBadge = toggle.querySelector('span');
        if (existingBadge) {
            existingBadge.remove();
        }
        
        // Add new badge if there are unread notifications
        if (unreadCount > 0) {
            const badge = document.createElement('span');
            badge.className = 'absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-medium';
            badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
            toggle.appendChild(badge);
        }
    }

    // --- Toggle dropdown with animation ---
    function toggleDropdown(e) {
        e.preventDefault();
        e.stopPropagation();
        
        if (dropdown.classList.contains("hidden")) {
            // Show dropdown and load notifications
            dropdown.classList.remove("hidden");
            loadNotifications();
            
            // Add smooth animation when showing
            dropdown.style.opacity = '0';
            dropdown.style.transform = 'translateY(-10px) scale(0.95)';
            
            requestAnimationFrame(() => {
                dropdown.style.transition = 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)';
                dropdown.style.opacity = '1';
                dropdown.style.transform = 'translateY(0) scale(1)';
            });
        } else {
            dropdown.classList.add("hidden");
        }
    }

    // --- Close dropdown when clicking outside ---
    function closeDropdownOnOutsideClick(e) {
        if (!dropdown.contains(e.target) && !toggle.contains(e.target)) {
            dropdown.classList.add("hidden");
        }
    }

    // --- Mark all as read ---
    async function markAllAsRead(e) {
        e.preventDefault();
        const csrf = getCSRFToken();
        if (!csrf) return console.error("CSRF token not found");

        try {
            const res = await fetch("/notifications/mark-read/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrf,
                    "Accept": "application/json",
                },
            });

            if (res.ok) {
                // Reload notifications to reflect changes
                loadNotifications();
            } else {
                console.error("Failed to mark notifications read:", res.status);
            }
        } catch (err) {
            console.error("Error marking notifications read:", err);
        }
    }

    // --- Clear (archive) all notifications ---
    async function clearAllNotifications(e) {
        e.preventDefault();
        const csrf = getCSRFToken();
        if (!csrf) return console.error("CSRF token not found");

        try {
            const res = await fetch("/notifications/clear/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrf,
                    "Accept": "application/json",
                },
            });

            if (res.ok) {
                // Show empty state
                notificationContent.innerHTML = `
                    <div class="text-center py-8 text-gray-500">
                        <svg class="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6 6 0 10-12 0v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                        </svg>
                        <p class="font-medium">All caught up!</p>
                        <p class="text-sm">No new notifications</p>
                    </div>
                `;
                
                // Remove badge
                const badge = toggle.querySelector("span");
                if (badge) badge.remove();
            } else {
                console.error("Failed to clear notifications:", res.status);
            }
        } catch (err) {
            console.error("Error clearing notifications:", err);
        }
    }

    // --- Event listeners ---
    if (toggle) toggle.addEventListener("click", toggleDropdown);
    if (markAllBtn) markAllBtn.addEventListener("click", markAllAsRead);
    if (clearAllBtn) clearAllBtn.addEventListener("click", clearAllNotifications);

    // Close dropdown on click outside
    document.addEventListener("click", closeDropdownOnOutsideClick);
    
    // Prevent dropdown from closing when clicking inside
    if (dropdown) {
        dropdown.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }

    // Load notifications on page load to show initial badge
    loadNotifications();
});