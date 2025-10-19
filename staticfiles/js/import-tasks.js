document.addEventListener("DOMContentLoaded", () => {
    const openPdfModal = document.getElementById("openPdfModal");
    const pdfModal = document.getElementById("pdfModal");
    const pdfForm = document.getElementById("pdfUploadForm");
    const preview = document.getElementById("importedPreview");
    const tableBody = document.getElementById("importedTableBody");
    const saveForm = document.getElementById("importedSaveForm");

    // Toggle modal
    openPdfModal.addEventListener("click", () => {
        pdfModal.classList.toggle("hidden");
    });

    // Upload file + preview
    pdfForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const url = pdfForm.dataset.importUrl;
        const formData = new FormData(pdfForm);

        const response = await fetch(url, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            alert("Failed to import file");
            return;
        }

        const data = await response.json(); // expect { tasks: [...] }
        tableBody.innerHTML = "";

        data.tasks.forEach((task, i) => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td><input type="text" name="task_name_${i}" value="${task.task_name}" class="border p-1 w-full"></td>
                <td><input type="date" name="start_${i}" value="${task.start}" class="border p-1 w-full"></td>
                <td><input type="date" name="end_${i}" value="${task.end}" class="border p-1 w-full"></td>
                <td><input type="number" name="days_${i}" value="${task.days}" class="border p-1 w-full"></td>
                <td><input type="number" name="mh_${i}" value="${task.mh}" class="border p-1 w-full"></td>
            `;
            tableBody.appendChild(row);
        });

        preview.classList.remove("hidden");
    });

    // Save imported tasks
    saveForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const url = saveForm.dataset.saveUrl;
        const formData = new FormData(saveForm);

        const response = await fetch(url, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            alert("Failed to save tasks");
            return;
        }

        alert("Tasks saved successfully!");
        preview.classList.add("hidden");
        pdfModal.classList.add("hidden");
    });
});
