document.addEventListener("DOMContentLoaded", function () {

  // Modal elements
  const modal = document.getElementById("projectTypeModal");
  const modalTitle = modal.querySelector("#modalTitle");
  const modalForm = modal.querySelector("#modalForm");
  const submitBtn = modal.querySelector("#modalSubmitBtn");

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

});
