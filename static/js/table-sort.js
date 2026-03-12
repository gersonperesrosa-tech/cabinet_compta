console.log("TABLE SORT LOADED");

document.addEventListener("DOMContentLoaded", () => {

    document.querySelectorAll("th[data-sort]").forEach(th => {
        th.style.cursor = "pointer";

        th.addEventListener("click", function () {

            let table = th.closest("table");
            let tbody = table.querySelector("tbody");
            let rows = Array.from(tbody.querySelectorAll("tr"));
            let index = Array.from(th.parentNode.children).indexOf(th);

            let current = th.dataset.order || "none";
            let newOrder = current === "asc" ? "desc" : "asc";

            // Reset icons
            table.querySelectorAll(".sort-icon").forEach(i => i.textContent = "⬍");

            // Set icon
            th.querySelector(".sort-icon").textContent = newOrder === "asc" ? "▲" : "▼";

            // Save order
            th.dataset.order = newOrder;

            rows.sort((a, b) => {
                let A = a.children[index].innerText.trim().toLowerCase();
                let B = b.children[index].innerText.trim().toLowerCase();

                // Try numeric comparison
                let numA = parseFloat(A.replace(",", "."));
                let numB = parseFloat(B.replace(",", "."));

                if (!isNaN(numA) && !isNaN(numB)) {
                    return newOrder === "asc" ? numA - numB : numB - numA;
                }

                // Fallback: string comparison
                return newOrder === "asc"
                    ? A.localeCompare(B)
                    : B.localeCompare(A);
            });

            rows.forEach(row => tbody.appendChild(row));
        });
    });

});
