console.log("Sidebar JS loaded!");
document.addEventListener("DOMContentLoaded", () => {
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebarClose = document.getElementById('sidebarClose');
  const sidebar = document.getElementById('sidebar');

  // Open sidebar (mobile)
  sidebarToggle?.addEventListener('click', () => {
    sidebar.classList.add('open');
  });

  // Close sidebar (mobile)
  sidebarClose?.addEventListener('click', () => {
    sidebar.classList.remove('open');
  });

  // Highlight active link
  document.querySelectorAll('.sidebar-menu-item > a').forEach(link => {
    link.addEventListener('click', () => {
      document.querySelectorAll('.sidebar-menu-item').forEach(item => 
        item.classList.remove('active', 'bg-blue-100')
      );
      link.parentElement.classList.add('active', 'bg-blue-100');
    });
  });

  // Toggle submenu
  document.querySelectorAll('[data-submenu-toggle]').forEach(button => {
    button.addEventListener('click', () => {
      const submenu = button.nextElementSibling;
      const arrow = button.querySelector('svg.ml-auto');
      submenu.classList.toggle('hidden');
      arrow.classList.toggle('rotate-180');
      button.parentElement.classList.toggle('bg-blue-50');
    });
  });

  // Fade out Django messages
  const container = document.getElementById('message-container');
  if (container) {
    setTimeout(() => {
      container.style.transition = "opacity 0.5s ease";
      container.style.opacity = 0;
      setTimeout(() => container.remove(), 500);
    }, 3000);
  }
});
