document.addEventListener("DOMContentLoaded", () => {
    
    const tableSearchInput = document.getElementById("tableSearchInput");
    const roleFilter = document.getElementById("roleFilter");
    const tableBody = document.getElementById("tableBody");


    if (!tableSearchInput || !roleFilter || !tableBody) {
        console.error("Required elements not found!");
        return;
    }

    // Grab all rows that contain user data
    const allRows = Array.from(tableBody.querySelectorAll("tr")).filter(row => 
        row.querySelector("td") && row.id !== "noProfilesRow"
    );


    const filterTable = () => {
        const query = tableSearchInput.value.toLowerCase().trim();
        const selectedRole = roleFilter.value;
        let visibleCount = 0;


        allRows.forEach((row, index) => {
            const email = row.cells[0]?.innerText.toLowerCase() || '';
            
            // Get the name from the display span, not input fields
            const nameSpan = row.querySelector('.name-text');
            const fullName = nameSpan ? nameSpan.innerText.toLowerCase() : '';
            
            const role = row.dataset.role || '';

            const matchesSearch = email.includes(query) || fullName.includes(query);
            const matchesRole = !selectedRole || role === selectedRole;


            if (matchesSearch && matchesRole) {
                row.style.display = "";
                visibleCount++;
            } else {
                row.style.display = "none";
            }
        });


        // Handle "No profiles found"
        let noRow = document.getElementById("noProfilesRow");
        if (noRow) {
            noRow.style.display = visibleCount === 0 ? "" : "none";
        }
    };

    const sortRowsByUpdated = () => {
        const rowsArray = allRows.slice();
        rowsArray.sort((a, b) => {
            const aTime = parseInt(a.dataset.updated) || 0;
            const bTime = parseInt(b.dataset.updated) || 0;
            return bTime - aTime;
        });
        rowsArray.forEach(row => tableBody.appendChild(row));
    };

    const updateTable = () => {
        console.log("updateTable called");
        filterTable();
        sortRowsByUpdated();
    };

    // Add event listeners with logging
    tableSearchInput.addEventListener("input", (e) => {
        updateTable();
    });
    
    roleFilter.addEventListener("change", (e) => {
        updateTable();
    });

    updateTable();
});