document.addEventListener("DOMContentLoaded", () => {

    // Load project JSON data
    const dataEl = document.getElementById("projects-data");
    if (!dataEl) return console.error("❌ No projects-data element found");
    
    let projects = [];
    try {
        projects = JSON.parse(dataEl.textContent);
    } catch (err) {
        return console.error("❌ Failed to parse projects JSON:", err);
    } 

    // ---------------------------
    // Horizontal Stacked Bar Chart
    // ---------------------------
    const chartEl = document.getElementById("progressChart");
    if (chartEl) {
        const ctx = chartEl.getContext("2d");

        new Chart(ctx, {
            type: "bar",
            data: {
                labels: projects.map(p => p.name),
                datasets: [
                    {
                        label: "Planned",
                        data: projects.map(p => p.planned_progress || 0),
                        backgroundColor: "rgba(249, 115, 22, 0.7)", // 🔶 orange
                        borderColor: "rgba(249, 115, 22, 1)",
                        borderWidth: 1
                    },
                    {
                        label: "Actual",
                        data: projects.map(p => p.actual_progress || 0),
                        backgroundColor: "rgba(139, 92, 246, 0.7)", // 🟣 purple
                        borderColor: "rgba(139, 92, 246, 1)",
                        borderWidth: 1
                    }
                ]
            },
            options: {
                indexAxis: "y", // horizontal bar
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "top" }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { callback: value => value + "%" }
                    },
                    y: {
                        ticks: { font: { size: 14 } }
                    }
                }
            }
        });
  
    }

    // ---------------------------
    // Task Calendar
    // ---------------------------
    const calendarEl = document.getElementById("taskCalendar");
    if (calendarEl) {
        const projectColors = {};
        const palette = [
            "#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6",
            "#EC4899", "#14B8A6", "#F97316", "#84CC16", "#06B6D4"
        ];

        let colorIndex = 0;
        projects.forEach(p => {
            const name = p.project_name || p.name || "Unknown Project";
            if (!projectColors[name]) {
                projectColors[name] = palette[colorIndex % palette.length];
                colorIndex++;
            }
        });

        const events = projects.flatMap(p =>
            (p.tasks || []).map(t => {
                const projectName = p.project_name || p.name || "Unknown Project";
                return {
                    title: t.title,
                    start: t.start,
                    end: t.end,
                    allDay: true,
                    color: projectColors[projectName],
                    extendedProps: {
                        progress: t.progress || 0,
                        project: projectName
                    }
                };
            })
        );

        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: "dayGridMonth",
            height: "100%",
            contentHeight: "100%",
            expandRows: true,
            headerToolbar: {
                left: "prev,next today",
                center: "title",
                right: "dayGridMonth,dayGridWeek,dayGridDay"
            },
            events,
            eventClick: function(info) {
                const task = info.event;
                document.getElementById("modalTitle").textContent = task.title;
                document.getElementById("modalBody").innerHTML = `
                    <p><strong>Project:</strong> ${task.extendedProps.project}</p>
                    <p><strong>Progress:</strong> ${task.extendedProps.progress}%</p>
                    <p><strong>Start:</strong> ${task.start.toLocaleDateString()}</p>
                    <p><strong>End:</strong> ${task.end ? task.end.toLocaleDateString() : "N/A"}</p>
                `;
                document.getElementById("taskModal").classList.remove("hidden");
            },
            eventDisplay: "block",
            views: {
                dayGridMonth: {},
                dayGridWeek: {},
                dayGridDay: {}
            }
        });

        calendar.render();
    }

// ---------------------------
// Budget Summary Line Chart
// ---------------------------
const budgetChartEl = document.getElementById("budgetChart");
if (budgetChartEl) {
    const plannedData = projects.map(p => Number(p.budget_total?.planned) || 0);
    const allocatedData = projects.map(p => Number(p.budget_total?.allocated) || 0);
    const spentData = projects.map(p => Number(p.budget_total?.spent) || 0);

    new Chart(budgetChartEl.getContext("2d"), {
        type: "line", // changed from 'bar' to 'line'
        data: {
            labels: projects.map(p => p.name),
            datasets: [
                { 
                    label: "Planned", 
                    data: plannedData, 
                    borderColor: "rgba(249,115,22,1)", 
                    backgroundColor: "rgba(249,115,22,0.2)",
                    fill: true,
                    tension: 0.3
                },
                { 
                    label: "Allocated", 
                    data: allocatedData, 
                    borderColor: "rgba(139,92,246,1)", 
                    backgroundColor: "rgba(139,92,246,0.2)",
                    fill: true,
                    tension: 0.3
                },
                { 
                    label: "Spent", 
                    data: spentData, 
                    borderColor: "rgba(34,197,94,1)", 
                    backgroundColor: "rgba(34,197,94,0.2)",
                    fill: true,
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: "top" } },
            scales: {
                y: { beginAtZero: true, ticks: { callback: v => "₱" + v.toLocaleString() } }
            }
        }
    });
}


});
