document.addEventListener("DOMContentLoaded", () => {
    // ---------- Add Project Dropdown ----------
    const button = document.getElementById("addProjectButton");
    const dropdown = document.getElementById("addProjectDropdown");

    if (button && dropdown) {
        button.addEventListener("click", (e) => {
            e.stopPropagation();
            dropdown.classList.toggle("hidden");
        });

        document.addEventListener("click", (e) => {
            if (!dropdown.contains(e.target) && !button.contains(e.target)) {
                dropdown.classList.add("hidden");
            }
        });
    }

    // Detect which dropdown item is clicked
    document.querySelectorAll("#addProjectDropdown a").forEach(link => {
        link.addEventListener("click", (e) => {
            e.preventDefault(); // Stop navigation for testing
            const type = link.dataset.type;
            window.location.href = link.href; // navigate
        });
    });

    // ---------- Project Table Search ----------
    const searchInput = document.getElementById("projectSearchInput");
    const tableBody = document.getElementById("projectTableBody");

    if (searchInput && tableBody) {
        const rows = Array.from(tableBody.querySelectorAll("tr"));

        searchInput.addEventListener("input", () => {
            const query = searchInput.value.toLowerCase().trim();
            let visibleCount = 0;

            rows.forEach(row => {
                const name = row.cells[0]?.innerText.toLowerCase() || '';
                const desc = row.cells[1]?.innerText.toLowerCase() || '';
                const match = name.includes(query) || desc.includes(query);

                row.style.display = match ? "" : "none";
                if (match) visibleCount++;
            });

            // Handle "No projects found"
            let noRow = document.getElementById("noProjectsRow");
            if (!noRow) {
                noRow = document.createElement("tr");
                noRow.id = "noProjectsRow";
                noRow.innerHTML = `<td colspan="6" class="text-center py-4 text-gray-500">No projects found.</td>`;
                tableBody.appendChild(noRow);
            }
            noRow.style.display = visibleCount === 0 ? "" : "none";
        });
    }


});

