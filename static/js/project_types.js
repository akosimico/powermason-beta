// Modal elements (defined globally)
let modal, modalTitle, modalForm, submitBtn;

document.addEventListener("DOMContentLoaded", function () {

  // Initialize modal elements
  modal = document.getElementById("projectTypeModal");
  modalTitle = modal.querySelector("#modalTitle");
  modalForm = modal.querySelector("#modalForm");
  submitBtn = modal.querySelector("#modalSubmitBtn");

  // Open Add Modal
  const addButtons = document.querySelectorAll("#addBtn, #emptyAddBtn");
  addButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      modalTitle.textContent = "Add Project Type";
      submitBtn.textContent = "Create";
      modalForm.reset();
      modalForm.action = btn.dataset.addUrl;
      modalForm.querySelector("#id_is_active").checked = true;
      modal.classList.remove("hidden");
    });
  });

  // Open Edit Modal
  const editButtons = document.querySelectorAll(".editBtn");
  editButtons.forEach(btn => {
    btn.addEventListener("click", async () => {
      const url = btn.dataset.url;
      const editUrl = btn.dataset.editUrl;
      try {
        const response = await fetch(url);
        const data = await response.json();
        modalTitle.textContent = "Edit Project Type";
        submitBtn.textContent = "Update";
        modalForm.action = editUrl;
        modalForm.querySelector("#id_name").value = data.name;
        modalForm.querySelector("#id_code").value = data.code;
        modalForm.querySelector("#id_description").value = data.description;
        modalForm.querySelector("#id_is_active").checked = data.is_active;
        modal.classList.remove("hidden");
      } catch (err) {
        alert("Failed to fetch project type data.");
        console.error(err);
      }
    });
  });

});

// Global function for edit button onclick (defined outside DOMContentLoaded)
console.log('Defining editProjectType function...');
window.editProjectType = async function(projectTypeId) {
    try {
      const response = await fetch(`/manage-client/api/project-types/${projectTypeId}/`);
      const data = await response.json();
      
      modalTitle.textContent = "Edit Project Type";
      submitBtn.textContent = "Update";
      modalForm.action = `/manage-client/project-types/edit/${projectTypeId}/`;
      
      // Set the project type ID for auto-configure functionality
      modalForm.querySelector("#projectTypeId").value = projectTypeId;
      
      // Populate form fields
      modalForm.querySelector("#id_name").value = data.name || '';
      modalForm.querySelector("#id_code").value = data.code || '';
      modalForm.querySelector("#id_description").value = data.description || '';
      modalForm.querySelector("#id_is_active").checked = data.is_active || false;
      
      // Populate cost configuration fields if they exist
      const costFields = {
        'base_cost_low_end': data.base_cost_low_end,
        'base_cost_mid_range': data.base_cost_mid_range,
        'base_cost_high_end': data.base_cost_high_end,
        'materials_percentage': data.materials_percentage,
        'labor_percentage': data.labor_percentage,
        'equipment_percentage': data.equipment_percentage,
        'permits_percentage': data.permits_percentage,
        'contingency_percentage': data.contingency_percentage,
        'overhead_percentage': data.overhead_percentage
      };
      
      for (const [fieldName, value] of Object.entries(costFields)) {
        const field = modalForm.querySelector(`[name="${fieldName}"]`);
        if (field && value !== null && value !== undefined) {
          field.value = value;
        }
      }
      
      modal.classList.remove("hidden");
    } catch (err) {
      alert("Failed to fetch project type data.");
      console.error(err);
    }
  };

  // Open Delete Modal
  const deleteButtons = document.querySelectorAll(".deleteBtn");
  const deleteModal = document.getElementById("deleteModal");
  const deleteForm = deleteModal.querySelector("#deleteForm");
  const deleteText = deleteModal.querySelector("#deleteText");

  deleteButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const name = btn.dataset.name;
      const usage = btn.dataset.usage;
      deleteForm.action = btn.dataset.deleteUrl;
      if (usage > 0) {
        deleteText.textContent = `Project type "${name}" is used in ${usage} project(s). It will be deactivated.`;
      } else {
        deleteText.textContent = `Are you sure you want to delete project type "${name}"? This action cannot be undone.`;
      }
      deleteModal.classList.remove("hidden");
    });
  });

  // --- CLOSE MODALS ---

  // 1. Close when clicking Cancel / ✕ buttons
  document.querySelectorAll(".modalClose").forEach(button => {
    button.addEventListener("click", () => {
      const modal = button.closest(".modal");
      if (modal) modal.classList.add("hidden");
    });
  });

  // 2. Close when clicking backdrop
  document.querySelectorAll(".modal").forEach(modal => {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        modal.classList.add("hidden");
      }
    });
  });

  // 3. Close when pressing Esc key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      document.querySelectorAll(".modal").forEach(modal => {
        if (!modal.classList.contains("hidden")) {
          modal.classList.add("hidden");
        }
      });
    }
  });

  // Auto-configure button functionality
  const autoConfigureBtn = document.getElementById("autoConfigureBtn");
  if (autoConfigureBtn) {
    autoConfigureBtn.addEventListener("click", handleAutoConfigure);
  }

});

// Auto-configure handler function
async function handleAutoConfigure() {
  const projectTypeId = modalForm.querySelector("#projectTypeId")?.value;
  if (!projectTypeId) {
    alert("Please save the project type first before auto-configuring costs.");
    return;
  }

  const originalText = this.textContent;
  this.textContent = "Configuring...";
  this.disabled = true;

  try {
    const response = await fetch(`/projects/api/project-type-auto-configure/${projectTypeId}/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'Content-Type': 'application/json'
      }
    });

    const result = await response.json();

    if (result.success) {
      // Update form fields with auto-configured values
      const costFields = {
        'base_cost_low_end': result.cost_data.base_cost_low_end,
        'base_cost_mid_range': result.cost_data.base_cost_mid_range,
        'base_cost_high_end': result.cost_data.base_cost_high_end,
        'materials_percentage': result.cost_data.materials_percentage,
        'labor_percentage': result.cost_data.labor_percentage,
        'equipment_percentage': result.cost_data.equipment_percentage,
        'permits_percentage': result.cost_data.permits_percentage,
        'contingency_percentage': result.cost_data.contingency_percentage,
        'overhead_percentage': result.cost_data.overhead_percentage
      };

      for (const [fieldName, value] of Object.entries(costFields)) {
        const field = modalForm.querySelector(`[name="${fieldName}"]`);
        if (field && value !== null && value !== undefined) {
          field.value = value;
        }
      }

      alert(`✅ ${result.message}`);
    } else {
      alert(`❌ ${result.error}`);
    }
  } catch (error) {
    console.error('Error auto-configuring costs:', error);
    alert("❌ Failed to auto-configure costs. Please try again.");
  } finally {
    this.textContent = originalText;
    this.disabled = false;
  }
}

// Helper function to get CSRF token
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
