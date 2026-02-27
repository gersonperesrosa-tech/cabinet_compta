(function() {

    // Récupération du token CSRF dans les cookies
    function getCSRFCookie() {
        const name = 'csrftoken';
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                return decodeURIComponent(cookie.substring(name.length + 1));
            }
        }
        return null;
    }

    // Création du menu horizontal de pastilles
    function createPalette(tvaId, mois, currentStatut, anchor) {

        const couleurs = [
            { code: "BLANC", label: "Blanc", color: "#FFFFFF" },
            { code: "JAUNE", label: "Jaune", color: "#FFD700" },
            { code: "VERT_CLAIR", label: "Vert clair", color: "#90EE90" },
            { code: "VERT_FONCE", label: "Vert foncé", color: "#006400" },
        ];

        const palette = document.createElement("div");
        palette.className = "tva-palette";

        couleurs.forEach(item => {
            const dot = document.createElement("span");
            dot.className = "tva-palette-dot";
            dot.style.backgroundColor = item.color;
            dot.title = item.label;

            if (item.code === currentStatut) {
                dot.classList.add("tva-palette-dot-active");
            }

            dot.addEventListener("click", function(e) {
                e.stopPropagation();
                setStatut(tvaId, mois, item.code, anchor, palette, item.color);
            });

            palette.appendChild(dot);
        });

        // Positionnement du menu à droite de la pastille
        const rect = anchor.getBoundingClientRect();
        palette.style.position = "absolute";
        palette.style.left = (window.scrollX + rect.right + 6) + "px";
        palette.style.top = (window.scrollY + rect.top - 4) + "px";

        document.body.appendChild(palette);

        // Fermeture du menu au clic extérieur
        function closePalette() {
            if (palette.parentNode) {
                palette.parentNode.removeChild(palette);
            }
            document.removeEventListener("click", closePalette);
        }

        setTimeout(function() {
            document.addEventListener("click", closePalette);
        }, 0);
    }

    // Envoi AJAX pour mettre à jour le statut
    function setStatut(tvaId, mois, statut, anchor, palette, color) {
        const csrfToken = getCSRFCookie();
        const xhr = new XMLHttpRequest();

        xhr.open("POST", "/tva/set-statut/");
        xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");

        if (csrfToken) {
            xhr.setRequestHeader("X-CSRFToken", csrfToken);
        }

        xhr.onload = function() {
            if (xhr.status === 200) {
                anchor.style.backgroundColor = color;
                anchor.setAttribute("data-statut", statut);
            }
            if (palette && palette.parentNode) {
                palette.parentNode.removeChild(palette);
            }
        };

        xhr.send(
            "tva_id=" + encodeURIComponent(tvaId) +
            "&mois=" + encodeURIComponent(mois) +
            "&statut=" + encodeURIComponent(statut)
        );
    }

    // Activation des pastilles au chargement de la page
    document.addEventListener("DOMContentLoaded", function() {
        document.querySelectorAll(".tva-pastille").forEach(function(pastille) {
            pastille.addEventListener("click", function(e) {
                e.stopPropagation();
                const tvaId = this.getAttribute("data-tva-id");
                const mois = this.getAttribute("data-mois");
                const statut = this.getAttribute("data-statut");
                createPalette(tvaId, mois, statut, this);
            });
        });
    });

})();