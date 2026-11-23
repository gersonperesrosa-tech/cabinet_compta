import json

from django.contrib.auth.models import User
from django.test import Client as DjangoClient, TestCase
from django.urls import reverse

from dossiers.models import Client
from .models import ClotureAnnee, ClotureExperimentaleCellule, ClotureExperimentaleLigne
from .views import _experimental_status


class TableauExperimentalClotureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("cabinet", password="secret")
        self.client.force_login(self.user)
        self.cloture = ClotureAnnee.objects.create(annee=2026)
        self.included_client = Client.objects.create(numero=10, nom="Alpha", forme_juridique="SARL")
        self.excluded_client = Client.objects.create(numero=20, nom="Beta", forme_juridique="SAS")
        self.cloture.clients.add(self.included_client)
        self.page_url = reverse("tableau_experimental_cloture")
        self.save_url = reverse("sauvegarder_cellule_experimentale")

    def _save(self, **updates):
        payload = {
            "cloture_id": self.cloture.id,
            "client_id": self.included_client.id,
            "column": "pre_revision",
            "text": "À contrôler",
            "color": "yellow",
            "version": 0,
        }
        payload.update(updates)
        return self.client.post(self.save_url, data=json.dumps(payload), content_type="application/json")

    def test_page_only_creates_rows_for_closure_clients(self):
        response = self.client.get(self.page_url, {"annee": 2026})
        self.assertContains(response, "Alpha")
        self.assertNotContains(response, '"client":"Beta"')
        self.assertEqual(ClotureExperimentaleLigne.objects.count(), 1)
        self.assertEqual(ClotureExperimentaleCellule.objects.count(), 17)

    def test_page_subscribes_to_tabulator_edit_and_selection_events(self):
        response = self.client.get(self.page_url, {"annee": 2026})
        self.assertContains(response, 'table.on("cellClick"')
        self.assertContains(response, 'table.on("cellEdited"')
        self.assertContains(response, 'table.on("dataFiltered"')
        self.assertNotContains(response, 'cellEdited: cell =>')

    def test_palette_keeps_the_selected_tabulator_cell_component(self):
        response = self.client.get(self.page_url, {"annee": 2026})
        self.assertContains(response, "activeCell = cell;")
        self.assertNotContains(response, "table.getRow(activeCell.rowId)")
        self.assertContains(response, 'editTriggerEvent: "dblclick"')
        self.assertContains(response, "experimental-active-cell")
        self.assertContains(response, "activeCellKey = {rowId: cell.getRow().getData().id, field: cell.getField()}")
        self.assertContains(response, "refreshActiveCellOutline();")

    def test_save_persists_text_color_and_recalculates_status(self):
        response = self._save()
        self.assertEqual(response.status_code, 200)
        line = ClotureExperimentaleLigne.objects.get()
        cell = line.cellules.get(colonne="pre_revision")
        self.assertEqual((cell.texte, cell.couleur), ("À contrôler", "yellow"))
        self.assertEqual(line.statut_general, "en_cours")

        version = response.json()["version"]
        response = self._save(color="dark_green", version=version)
        self.assertEqual(response.status_code, 200)
        line.refresh_from_db()
        self.assertEqual(line.statut_general, "en_cours")  # les autres cellules restent blanches

    def test_color_is_independent_from_text_and_persists_after_reload(self):
        response = self._save(text="Texte conservé", color="yellow")
        self.assertEqual(response.status_code, 200)

        response = self._save(
            text="Texte conservé",
            color="red",
            version=response.json()["version"],
        )
        self.assertEqual(response.status_code, 200)
        cell = ClotureExperimentaleCellule.objects.get(colonne="pre_revision")
        self.assertEqual((cell.texte, cell.couleur), ("Texte conservé", "red"))

        response = self.client.get(self.page_url, {"annee": 2026})
        self.assertEqual(response.context["table_rows"][0]["pre_revision"], "Texte conservé")
        self.assertEqual(response.context["table_rows"][0]["colors"]["pre_revision"], "red")

    def test_all_palette_colors_are_accepted(self):
        version = 0
        for color in ("none", "gray", "yellow", "orange", "light_green", "dark_green", "red"):
            response = self._save(text="", color=color, version=version)
            self.assertEqual(response.status_code, 200)
            version = response.json()["version"]
            self.assertEqual(
                ClotureExperimentaleCellule.objects.get(colonne="pre_revision").couleur,
                color,
            )

    def test_successive_changes_on_one_line_persist_after_reload(self):
        first = self._save(text="Première étape", color="yellow")
        self.assertEqual(first.status_code, 200)
        second = self._save(
            column="relance_pieces",
            text="Deuxième étape",
            color="dark_green",
            version=first.json()["version"],
        )
        self.assertEqual(second.status_code, 200)

        response = self.client.get(self.page_url, {"annee": 2026})
        row = response.context["table_rows"][0]
        self.assertEqual(row["pre_revision"], "Première étape")
        self.assertEqual(row["colors"]["pre_revision"], "yellow")
        self.assertEqual(row["relance_pieces"], "Deuxième étape")
        self.assertEqual(row["colors"]["relance_pieces"], "dark_green")
        self.assertEqual(row["version"], second.json()["version"])

    def test_page_issues_csrf_cookie_for_ajax_save(self):
        csrf_client = DjangoClient(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        page = csrf_client.get(self.page_url, {"annee": 2026})
        self.assertIn("csrftoken", page.cookies)

        payload = {
            "cloture_id": self.cloture.id,
            "client_id": self.included_client.id,
            "column": "pre_revision",
            "text": "Sauvegarde AJAX",
            "color": "yellow",
            "version": 0,
        }
        response = csrf_client.post(
            self.save_url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=page.cookies["csrftoken"].value,
        )
        self.assertEqual(response.status_code, 200)

    def test_all_gray_or_dark_green_is_completed_and_stale_write_is_rejected(self):
        self.client.get(self.page_url, {"annee": 2026})
        line = ClotureExperimentaleLigne.objects.get()
        line.cellules.update(couleur="gray")
        line.version = 4
        line.save(update_fields=("version",))
        response = self._save(color="dark_green", version=4)
        self.assertEqual(response.status_code, 200)
        line.refresh_from_db()
        self.assertEqual(line.statut_general, "termine")
        stale_response = self._save(version=4)
        self.assertEqual(stale_response.status_code, 409)

    def test_invalid_color_and_client_outside_closure_are_rejected(self):
        self.assertEqual(self._save(color="blue").status_code, 400)
        self.assertEqual(self._save(client_id=self.excluded_client.id).status_code, 404)

    def test_status_rules_apply_in_the_required_priority_order(self):
        self.assertEqual(_experimental_status(["none"] * 17), "non_commence")
        self.assertEqual(_experimental_status(["gray", "dark_green"] * 8 + ["gray"]), "termine")
        self.assertEqual(_experimental_status(["none", "gray"] + ["dark_green"] * 15), "en_cours")
