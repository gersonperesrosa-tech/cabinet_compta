/* ---------------------------------------------------------
   TOGGLE SIDEBAR GAUCHE
--------------------------------------------------------- */
const toggleBtn = document.getElementById("toggleSidebar");
const sidebar = document.getElementById("sidebar");
const dashboardContainer = document.querySelector(".container-dashboard");

toggleBtn.addEventListener("click", () => {
    sidebar.classList.toggle("collapsed");
    dashboardContainer.classList.toggle("sidebar-collapsed");
});

/* ---------------------------------------------------------
   CALENDRIER INTERACTIF
--------------------------------------------------------- */
let currentDate = new Date();

function renderCalendar(date) {
    const container = document.getElementById("calendar-container");
    const title = document.getElementById("calendar-title");

    if (!container || !title) return;

    const year = date.getFullYear();
    const month = date.getMonth();

    const monthNames = [
        "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
        "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
    ];

    title.textContent = `${monthNames[month]} ${year}`;

    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    const days = ["L", "M", "M", "J", "V", "S", "D"];

    let html = "<table class='calendar-table'>";
    html += "<tr>" + days.map(d => `<th>${d}</th>`).join("") + "</tr><tr>";

    let dayOfWeek = firstDay === 0 ? 6 : firstDay - 1;

    for (let i = 0; i < dayOfWeek; i++) {
        html += "<td></td>";
    }

    const today = new Date();

    for (let day = 1; day <= daysInMonth; day++) {
        const isToday =
            day === today.getDate() &&
            month === today.getMonth() &&
            year === today.getFullYear();

        html += `<td class="${isToday ? "today" : ""}">${day}</td>`;

        dayOfWeek++;
        if (dayOfWeek === 7) {
            html += "</tr><tr>";
            dayOfWeek = 0;
        }
    }

    html += "</tr></table>";
    container.innerHTML = html;
}

const prevBtn = document.getElementById("prev-month");
const nextBtn = document.getElementById("next-month");

if (prevBtn && nextBtn) {
    prevBtn.addEventListener("click", () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        renderCalendar(currentDate);
    });

    nextBtn.addEventListener("click", () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        renderCalendar(currentDate);
    });

    renderCalendar(currentDate);
}

/* ---------------------------------------------------------
   CERCLE CA3M
--------------------------------------------------------- */
function updateCA3MCircle(value) {
    const circle = document.querySelector(".circle-chart");
    const text = document.getElementById("ca3m-value");

    if (!circle || !text) return;

    text.textContent = value + "%";

    circle.style.borderTopColor = "var(--blue)";
    circle.style.borderRightColor = value > 25 ? "var(--blue)" : "var(--grey-medium)";
    circle.style.borderBottomColor = value > 50 ? "var(--blue)" : "var(--grey-medium)";
    circle.style.borderLeftColor = value > 75 ? "var(--blue)" : "var(--grey-medium)";
}

updateCA3MCircle(45);

/* ---------------------------------------------------------
   FILTRES DU TABLEAU CLIENTS
--------------------------------------------------------- */
function addTableFilters() {
    const table = document.querySelector(".client-table");
    if (!table) return;

    const thead = table.querySelector("thead");
    const headerCells = thead.querySelectorAll("th");

    const filterRow = document.createElement("tr");

    headerCells.forEach((th, index) => {
        const td = document.createElement("td");

        const input = document.createElement("input");
        input.type = "text";
        input.placeholder = "Filtrer...";
        input.dataset.col = index;
        input.classList.add("table-filter");

        input.addEventListener("keyup", filterTable);

        td.appendChild(input);
        filterRow.appendChild(td);
    });

    thead.appendChild(filterRow);
}

function filterTable() {
    const table = document.querySelector(".client-table");
    const filters = document.querySelectorAll(".table-filter");
    const rows = table.querySelectorAll("tbody tr");

    rows.forEach(row => {
        let visible = true;

        filters.forEach((input, colIndex) => {
            const filterValue = input.value.toLowerCase().trim();
            const cellText = row.children[colIndex].textContent.toLowerCase();

            if (filterValue !== "" && !cellText.includes(filterValue)) {
                visible = false;
            }
        });

        row.style.display = visible ? "" : "none";
    });
}

document.addEventListener("DOMContentLoaded", addTableFilters);

/* ---------------------------------------------------------
   SLIDEBAR DROIT : ouverture + chargement AJAX
--------------------------------------------------------- */
document.addEventListener("DOMContentLoaded", () => {

    document.querySelectorAll(".ligne-client").forEach(row => {
        row.addEventListener("click", () => {
            const clientId = row.dataset.client;

            fetch(`/suivi-comptable/formulaire/${clientId}/`)
                .then(response => response.text())
                .then(html => {
                    document.getElementById("slidebar-content").innerHTML = html;

                    document.getElementById("slidebar-droit").classList.add("open");
                    openOverlay();
                });
        });
    });

    const closeBtn = document.getElementById("closeSlidebar");
    if (closeBtn) {
        closeBtn.addEventListener("click", () => {
            document.getElementById("slidebar-droit").classList.remove("open");
            closeOverlay();
        });
    }
});

/* ---------------------------------------------------------
   SLIDEBAR DROIT : ouverture pour TVA MENSUELLE
--------------------------------------------------------- */
document.addEventListener("DOMContentLoaded", () => {

    if (window.location.pathname.startsWith("/tva-mensuelle")) {

        document.querySelectorAll(".ligne-client-tva").forEach(row => {
            row.addEventListener("click", () => {
                const clientId = row.dataset.client;

                fetch(`/tva-mensuelle/formulaire/${clientId}/`)
                    .then(response => response.text())
                    .then(html => {
                        document.getElementById("slidebar-content").innerHTML = html;

                        document.getElementById("slidebar-droit").classList.add("open");
                        openOverlay();
                    });
            });
        });
    }
});

/* ---------------------------------------------------------
   SLIDEBAR DROIT : sauvegarde AJAX
--------------------------------------------------------- */
document.addEventListener("submit", function (e) {
    if (e.target && e.target.id === "form-suivi") {
        e.preventDefault();

        const form = e.target;
        const clientId = form.dataset.client;

        const formData = new FormData(form);

        fetch(`/suivi-comptable/save/${clientId}/`, {
            method: "POST",
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {

                // Fermer le slidebar
                document.getElementById("slidebar-droit").classList.remove("open");
                closeOverlay();

                // 🔥 Mise à jour automatique de la ligne du tableau
                document.getElementById(`date_maj_${data.client_id}`).textContent = data.date_maj;
                document.getElementById(`mois_${data.client_id}`).textContent = data.dernier_mois_traite;
                document.getElementById(`saisi_${data.client_id}`).textContent = data.saisi_par;
                document.getElementById(`verifie_${data.client_id}`).textContent = data.verifie;

                // (Optionnel) Effet visuel sur la ligne mise à jour
                const row = document.querySelector(`tr[data-client="${data.client_id}"]`);
                if (row) {
                    row.classList.add("row-updated");
                    setTimeout(() => row.classList.remove("row-updated"), 1200);
                }

                console.log("Enregistré !");
            } else {
                console.error("Erreurs :", data.errors);
            }
        })
        .catch(error => {
            console.error("Erreur AJAX :", error);
        });
    }
});

/* ---------------------------------------------------------
   OVERLAY : ouverture / fermeture
--------------------------------------------------------- */
function openOverlay() {
    document.getElementById("overlay").classList.add("visible");
}

function closeOverlay() {
    document.getElementById("overlay").classList.remove("visible");
}

document.getElementById("overlay").addEventListener("click", () => {
    document.getElementById("slidebar-droit").classList.remove("open");
    closeOverlay();
});


// Fonction utilitaire pour récupérer le CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/* ---------------------------------------------------------
   SLIDEBAR DROIT : sauvegarde TVA mensuelle (listener délégué)
--------------------------------------------------------- */
document.addEventListener("submit", function (e) {
    if (e.target && e.target.id === "form-tva-mensuelle") {
        e.preventDefault();

        const form = e.target;
        const clientId = form.dataset.client;

        const formData = new FormData(form);

        fetch(`/tva-mensuelle/save/${clientId}/`, {
            method: "POST",
            body: formData,
            headers: {
                "X-CSRFToken": getCookie("csrftoken")
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {

                document.getElementById("slidebar-droit").classList.remove("open");
                closeOverlay();

                location.reload();
            }
        })
        .catch(error => {
            console.error("Erreur AJAX TVA :", error);
        });
    }
});


// ---------------------------------------------------------
//   PASTILLES TVA : ouverture du slidebar au clic
// ---------------------------------------------------------
document.addEventListener("click", function(e) {
    if (e.target.classList.contains("pastille")) {
        const clientId = e.target.dataset.client;

        fetch(`/tva-mensuelle/formulaire/${clientId}/`)
            .then(response => response.text())
            .then(html => {
                document.getElementById("slidebar-content").innerHTML = html;
                document.getElementById("slidebar-droit").classList.add("open");
                openOverlay();
            });
    }
});