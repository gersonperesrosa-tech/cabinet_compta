import re
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from dossiers.models import Client

from . import urls as fs_urls
from .models import (
    PrestataireSocial,
    PrestationSociale,
    TarifPrestataire,
    TypePrestation,
)


class _BatchFormReader(HTMLParser):
    """Reconstitue ce qu'un navigateur enverrait pour <form id="batch-form">.

    Ignore le contenu des <template>, les champs désactivés, les cases non
    cochées et les champs rattachés à un autre formulaire (attribut form).
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_form = False
        self.template_depth = 0
        self.select_name = None
        self.select_value = None
        self.select_first = None
        self.option_value = None
        self.fields = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "template":
            self.template_depth += 1
        if self.template_depth:
            return
        if tag == "form" and attrs.get("id") == "batch-form":
            self.in_form = True
        if not self.in_form or "disabled" in attrs:
            return
        if attrs.get("form") not in (None, "batch-form"):
            return
        name = attrs.get("name")
        if tag == "input" and name:
            kind = attrs.get("type", "text")
            if kind in ("button", "submit", "reset"):
                return
            if kind in ("checkbox", "radio"):
                if "checked" in attrs:
                    self.fields.append((name, attrs.get("value", "on")))
                return
            self.fields.append((name, attrs.get("value", "")))
        elif tag == "select" and name:
            self.select_name, self.select_value, self.select_first = name, None, None
        elif tag == "option" and self.select_name:
            value = attrs.get("value", "")
            if self.select_first is None:
                self.select_first = value
            if "selected" in attrs:
                self.select_value = value

    def handle_endtag(self, tag):
        if tag == "template":
            self.template_depth -= 1
        elif tag == "form" and self.in_form and not self.template_depth:
            self.in_form = False
        elif tag == "select" and self.select_name:
            value = self.select_value if self.select_value is not None else self.select_first
            self.fields.append((self.select_name, value or ""))
            self.select_name = None


def submitted_fields(response):
    reader = _BatchFormReader()
    reader.feed(response.content.decode())
    return reader.fields


class DonneesFacturationSociale:
    """Jeu de données et aides communs aux tests de l'app."""

    def setUp(self):
        self.client.force_login(User.objects.create_user("cabinet", is_staff=True))
        self.client_a = Client.objects.create(nom="Alpha", forme_juridique="SARL")
        self.client_b = Client.objects.create(nom="Beta", forme_juridique="SAS")
        self.prestation = TypePrestation.objects.create(
            nom="Bulletin", tarif_client_standard=Decimal("50.00")
        )
        self.prestation_2 = TypePrestation.objects.create(
            nom="DSN", tarif_client_standard=Decimal("80.00")
        )
        self.prestataire = PrestataireSocial.objects.create(nom="Partenaire A")
        self.prestataire_2 = PrestataireSocial.objects.create(nom="Partenaire B")
        TarifPrestataire.objects.create(
            prestation=self.prestation,
            prestataire=self.prestataire,
            cout_unitaire=Decimal("20.00"),
        )
        TarifPrestataire.objects.create(
            prestation=self.prestation,
            prestataire=self.prestataire_2,
            cout_unitaire=Decimal("25.00"),
        )
        TarifPrestataire.objects.create(
            prestation=self.prestation_2,
            prestataire=self.prestataire,
            cout_unitaire=Decimal("30.00"),
        )
        self.url = reverse("facturation_sociale:prestations_par_client")

    def payload(self, rows, client=None, token="test-token"):
        data = {
            "client": str((client or self.client_a).pk),
            "mois": "4",
            "annee": "2026",
            "submission_id": token,
            "form-TOTAL_FORMS": str(len(rows)),
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "500",
        }
        defaults = {
            "id": "",
            "prestation": str(self.prestation.pk),
            "prestataire": str(self.prestataire.pk),
            "quantite": "1.00",
            "detail": "",
            "mode_tarification": "standard",
            "tarif_client_personnalise": "",
            "motif_tarif_personnalise": "",
            "mode_cout_prestataire": "standard",
            "cout_prestataire_personnalise": "",
            "motif_cout_prestataire_personnalise": "",
            "deja_facturee": "",
            "DELETE": "",
        }
        for index, row in enumerate(rows):
            values = {**defaults, **row}
            for field, value in values.items():
                data[f"form-{index}-{field}"] = value
        return data

    def create_existing(self, client=None, **overrides):
        values = {
            "client": client or self.client_a,
            "prestation": self.prestation,
            "prestataire": self.prestataire,
            "mois": 4,
            "annee": 2026,
            "quantite": Decimal("1.00"),
            "tarif_client_standard_snapshot": Decimal("50.00"),
            "tarif_client_applique": Decimal("50.00"),
            "cout_prestataire_standard_snapshot": Decimal("20.00"),
            "cout_prestataire_unitaire_snapshot": Decimal("20.00"),
        }
        values.update(overrides)
        return PrestationSociale.objects.create(**values)


class PrestationsParClientTests(DonneesFacturationSociale, TestCase):
    def test_creates_multiple_identical_prestations(self):
        response = self.client.post(self.url, self.payload([{}, {"detail": "Paul"}]))
        self.assertRedirects(response, f"{self.url}?client={self.client_a.pk}&mois=4&annee=2026")
        self.assertEqual(PrestationSociale.objects.count(), 2)
        self.assertEqual(
            PrestationSociale.objects.filter(prestation=self.prestation).count(), 2
        )

    def test_client_must_be_selected_before_the_period_is_enabled_or_loaded(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'id="scope-mois" name="mois" disabled')
        self.assertContains(response, 'id="scope-annee" name="annee"')
        self.assertNotContains(response, 'id="prestations-table"')

        response = self.client.get(f"{self.url}?client={self.client_a.pk}")
        self.assertContains(response, "Sélectionnez un mois et une année valides.")
        self.assertNotContains(response, 'id="prestations-table"')

    def test_loads_and_updates_existing_line_without_duplication(self):
        line = self.create_existing(detail="Avant")
        response = self.client.get(f"{self.url}?client={self.client_a.pk}&mois=4&annee=2026")
        self.assertContains(response, f'value="{line.pk}"', html=False)

        response = self.client.post(
            self.url,
            self.payload([{"id": str(line.pk), "detail": "Après", "quantite": "2.00"}]),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(PrestationSociale.objects.count(), 1)
        line.refresh_from_db()
        self.assertEqual(line.detail, "Après")
        self.assertEqual(line.quantite, Decimal("2.00"))
        self.assertEqual(line.montant_facture, Decimal("100.00"))

    def test_adds_a_line_to_an_already_populated_period(self):
        line = self.create_existing()
        response = self.client.post(
            self.url,
            self.payload([{"id": str(line.pk)}, {"detail": "Nouvelle ligne"}]),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            PrestationSociale.objects.filter(
                client=self.client_a, mois=4, annee=2026
            ).count(),
            2,
        )

    def test_quantity_or_detail_change_keeps_historical_prices(self):
        line = self.create_existing()
        self.prestation.tarif_client_standard = Decimal("99.00")
        self.prestation.save()
        TarifPrestataire.objects.filter(
            prestation=self.prestation, prestataire=self.prestataire
        ).update(cout_unitaire=Decimal("77.00"))

        self.client.post(
            self.url,
            self.payload([{"id": str(line.pk), "quantite": "3.00", "detail": "Historique"}]),
        )
        line.refresh_from_db()
        self.assertEqual(line.tarif_client_applique, Decimal("50.00"))
        self.assertEqual(line.cout_prestataire_unitaire_snapshot, Decimal("20.00"))
        self.assertEqual(line.marge, Decimal("90.00"))

    def test_client_and_provider_exceptions_and_return_to_standard(self):
        line = self.create_existing()
        self.client.post(
            self.url,
            self.payload([{
                "id": str(line.pk),
                "mode_tarification": "personnalise",
                "tarif_client_personnalise": "55.00",
                "motif_tarif_personnalise": "Négocié",
                "mode_cout_prestataire": "personnalise",
                "cout_prestataire_personnalise": "18.00",
                "motif_cout_prestataire_personnalise": "Remise",
            }]),
        )
        line.refresh_from_db()
        self.assertTrue(line.tarif_personnalise)
        self.assertTrue(line.cout_prestataire_personnalise)
        self.assertEqual(line.marge, Decimal("37.00"))

        self.client.post(self.url, self.payload([{"id": str(line.pk)}], token="return"))
        line.refresh_from_db()
        self.assertFalse(line.tarif_personnalise)
        self.assertFalse(line.cout_prestataire_personnalise)
        self.assertEqual(line.tarif_client_applique, Decimal("50.00"))
        self.assertEqual(line.cout_prestataire_unitaire_snapshot, Decimal("20.00"))

    def test_deletion_and_cancellation_are_explicit(self):
        line = self.create_existing()
        self.client.post(
            self.url,
            self.payload([{"id": str(line.pk), "DELETE": ""}], token="cancel"),
        )
        self.assertTrue(PrestationSociale.objects.filter(pk=line.pk).exists())

        self.client.post(
            self.url,
            self.payload([{"id": str(line.pk), "DELETE": "on"}], token="delete"),
        )
        self.assertFalse(PrestationSociale.objects.filter(pk=line.pk).exists())

    def test_invalid_line_rolls_back_the_whole_batch(self):
        line = self.create_existing(detail="Non modifiée")
        response = self.client.post(
            self.url,
            self.payload([
                {"id": str(line.pk), "detail": "Modification à annuler"},
                {
                    "prestation": str(self.prestation_2.pk),
                    "prestataire": str(self.prestataire_2.pk),
                },
            ]),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PrestationSociale.objects.count(), 1)
        line.refresh_from_db()
        self.assertEqual(line.detail, "Non modifiée")
        self.assertContains(response, "Aucun tarif actif")

    def test_cannot_modify_or_delete_another_client_line(self):
        other_line = self.create_existing(client=self.client_b)
        response = self.client.post(
            self.url,
            self.payload([{"id": str(other_line.pk), "DELETE": "on"}]),
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PrestationSociale.objects.filter(pk=other_line.pk).exists())

    def test_duplicate_submission_token_does_not_duplicate_rows(self):
        data = self.payload([{}], token="same-token")
        self.client.post(self.url, data)
        self.client.post(self.url, data)
        self.assertEqual(PrestationSociale.objects.count(), 1)

    def test_existing_prestations_are_not_already_billed_by_default(self):
        line = self.create_existing()
        line.refresh_from_db()
        self.assertFalse(line.deja_facturee)

    def test_batch_entry_checks_and_unchecks_the_flag(self):
        line = self.create_existing()
        page = f"{self.url}?client={self.client_a.pk}&mois=4&annee=2026"

        self.client.post(
            self.url,
            self.payload(
                [{"id": str(line.pk), "deja_facturee": "on"}, {"deja_facturee": "on"}],
                token="check",
            ),
        )
        self.assertEqual(PrestationSociale.objects.filter(deja_facturee=True).count(), 2)
        formset = self.client.get(page).context["formset"]
        self.assertTrue(all(form["deja_facturee"].value() for form in formset))

        self.client.post(self.url, self.payload([{"id": str(line.pk)}], token="uncheck"))
        line.refresh_from_db()
        self.assertFalse(line.deja_facturee)

    def gestion(self, extra=""):
        return self.client.get(
            reverse("facturation_sociale:gestion") + "?mois=4&annee=2026" + extra
        )

    def billing_line(self, client, montant, billed=False, **overrides):
        return self.create_existing(
            client=client,
            tarif_client_applique=Decimal(montant),
            deja_facturee=billed,
            **overrides,
        )

    def create_clients_a_and_b(self):
        self.billing_line(self.client_a, "100.00")
        self.billing_line(self.client_b, "50.00", billed=True)
        self.billing_line(self.client_b, "30.00")

    def displayed_clients(self, response):
        return [item["client"] for item in response.context["synthese_clients"]]

    def test_gestion_totals_and_synthesis(self):
        self.create_clients_a_and_b()
        context = self.gestion().context

        self.assertEqual(context["total_prestations"], Decimal("180.00"))
        self.assertEqual(context["total_deja_facture"], Decimal("50.00"))
        self.assertEqual(context["total_reste"], Decimal("130.00"))
        self.assertEqual(context["total_cout"], Decimal("60.00"))
        self.assertEqual(context["total_marge"], Decimal("120.00"))
        self.assertEqual(context["nombre_clients"], 2)
        self.assertEqual(context["nombre_clients_a_facturer"], 2)

        beta = context["synthese_clients"][1]
        self.assertEqual(
            [beta[k] for k in ("total", "deja_facture", "reste", "cout", "marge")],
            [Decimal(n) for n in ("80", "50", "30", "40", "40")],
        )
        self.assertEqual(len(beta["lignes"]), 2)
        self.assertEqual(beta["statut"], "a_facturer")

        bulletin = context["synthese_prestations"][0]
        self.assertEqual(bulletin["quantite"], Decimal("3"))
        self.assertEqual(bulletin["total"], Decimal("180.00"))
        self.assertEqual(bulletin["deja_facture"], Decimal("50.00"))
        self.assertEqual(bulletin["reste"], Decimal("130.00"))

    def test_gestion_filter_hides_only_fully_billed_clients(self):
        self.create_clients_a_and_b()
        self.assertEqual(
            self.displayed_clients(self.gestion("&a_facturer=1")),
            [self.client_a, self.client_b],
        )

        client_c = Client.objects.create(nom="Gamma", forme_juridique="SAS")
        self.billing_line(client_c, "70.00", billed=True)

        full = self.gestion()
        self.assertEqual(
            self.displayed_clients(full), [self.client_a, self.client_b, client_c]
        )
        self.assertEqual(full.context["synthese_clients"][2]["statut"], "tout_facture")

        filtered = self.gestion("&a_facturer=1")
        self.assertEqual(
            self.displayed_clients(filtered), [self.client_a, self.client_b]
        )
        # Les cartes restent sur tout le mois ; le pied de tableau suit le filtre.
        self.assertEqual(filtered.context["total_prestations"], Decimal("250.00"))
        self.assertEqual(filtered.context["total_deja_facture"], Decimal("120.00"))
        self.assertEqual(filtered.context["nombre_clients"], 3)
        self.assertEqual(filtered.context["nombre_clients_a_facturer"], 2)
        self.assertEqual(filtered.context["totaux_affiches"]["total"], Decimal("180.00"))
        # Le filtre est conservé en changeant de mois.
        self.assertContains(filtered, "?mois=3&annee=2026&a_facturer=1")
        self.assertContains(filtered, "?mois=5&annee=2026&a_facturer=1")
        self.assertNotContains(full, "&a_facturer=1")

    def test_gestion_page_is_read_only_and_formats_amounts(self):
        line = self.billing_line(
            self.client_a,
            "1234.50",
            billed=True,
            tarif_personnalise=True,
            motif_tarif_personnalise='Accord "2026"',
            cout_prestataire_personnalise=True,
        )
        response = self.gestion()

        self.assertContains(response, "1\xa0234,50")
        self.assertContains(
            response,
            'title="Tarif exceptionnel · standard 50,00 € · Motif : Accord &quot;2026&quot;"',
        )
        self.assertContains(response, 'title="Coût exceptionnel · standard 20,00 €"')
        self.assertContains(
            response,
            f"{self.url}?client={self.client_a.pk}&mois=4&annee=2026",
        )
        self.assertNotContains(
            response,
            reverse("facturation_sociale:modifier_prestation_sociale", args=[line.pk]),
        )


class SaisieUniqueTests(DonneesFacturationSociale, TestCase):
    """La Saisie est la seule page de création et de modification."""

    def page_url(self, client=None, mois=4, annee=2026):
        return f"{self.url}?client={(client or self.client_a).pk}&mois={mois}&annee={annee}"

    def archive(self, client):
        client.archive = True
        client.save()

    def test_new_prestation_url_redirects_with_period(self):
        url = reverse("facturation_sociale:nouvelle_prestation")
        self.assertRedirects(self.client.get(url), self.url)
        self.assertRedirects(
            self.client.get(f"{url}?mois=4&annee=2026"), f"{self.url}?mois=4&annee=2026"
        )

    def test_edit_url_redirects_to_the_client_and_month_of_the_line(self):
        line = self.create_existing(client=self.client_b, mois=7, annee=2025)
        url = reverse("facturation_sociale:modifier_prestation_sociale", args=[line.pk])
        target = self.page_url(self.client_b, 7, 2025)
        self.assertRedirects(self.client.get(url), target)

        # Un POST n'est plus traité : rien ne change.
        self.assertRedirects(self.client.post(url, {"detail": "Ignoré"}), target)
        line.refresh_from_db()
        self.assertEqual(line.detail, "")

        missing = reverse("facturation_sociale:modifier_prestation_sociale", args=[999])
        self.assertEqual(self.client.get(missing).status_code, 404)

    def test_saisie_alias(self):
        url = reverse("facturation_sociale:saisie")
        self.assertEqual(url, "/facturation-sociale/saisie/")
        response = self.client.get(f"{url}?client={self.client_a.pk}&mois=4&annee=2026")
        self.assertEqual(response.context["selected_client"], self.client_a)

    def test_menu_marks_the_active_entry(self):
        saisie = reverse("facturation_sociale:saisie")
        cases = {
            saisie: saisie,
            self.url: saisie,
            reverse("facturation_sociale:gestion"): reverse("facturation_sociale:gestion"),
            reverse("facturation_sociale:configurations"):
                reverse("facturation_sociale:configurations"),
        }
        for page, active in cases.items():
            with self.subTest(page=page):
                content = self.client.get(page).content.decode()
                self.assertNotIn("Nouvelle prestation", content)
                self.assertEqual(
                    re.findall(r'active"\s+href="(/facturation-sociale/[^"]*)"', content),
                    [active],
                )

    def test_archived_client_is_accepted_only_with_lines_on_the_period(self):
        line = self.create_existing()
        self.archive(self.client_a)

        response = self.client.get(self.page_url())
        self.assertEqual(response.context["selected_client"], self.client_a)
        self.assertContains(response, "Client archivé</span>")
        self.assertNotIn(self.client_a, response.context["clients"])
        self.assertNotContains(response, 'id="add-line" class=')
        self.assertContains(response, 'id="scope-mois" name="mois" disabled')

        # Le lien « Saisir » de Gestion et l'ancienne URL de modification y mènent.
        gestion = self.client.get(
            reverse("facturation_sociale:gestion") + "?mois=4&annee=2026"
        )
        self.assertContains(gestion, self.page_url())
        self.assertRedirects(
            self.client.get(
                reverse("facturation_sociale:modifier_prestation_sociale", args=[line.pk])
            ),
            self.page_url(),
        )

        response = self.client.get(self.page_url(mois=5))
        self.assertIsNone(response.context["selected_client"])
        self.assertContains(response, "Le client sélectionné est invalide ou archivé.")

    def test_archived_client_lines_can_be_modified_but_not_added(self):
        line = self.create_existing()
        self.archive(self.client_a)

        response = self.client.post(
            self.url,
            self.payload([{"id": str(line.pk), "detail": "Refusé"}, {}], token="ajout"),
        )
        self.assertContains(response, "aucune nouvelle ligne ne peut être ajoutée")
        self.assertEqual(PrestationSociale.objects.count(), 1)
        line.refresh_from_db()
        self.assertEqual(line.detail, "")

        response = self.client.post(
            self.url,
            self.payload([{"id": str(line.pk), "detail": "Corrigé"}], token="modif"),
        )
        self.assertRedirects(response, self.page_url())
        line.refresh_from_db()
        self.assertEqual(line.detail, "Corrigé")

    def test_deleting_the_last_line_of_an_archived_client_returns_to_gestion(self):
        line = self.create_existing()
        self.archive(self.client_a)
        response = self.client.post(
            self.url, self.payload([{"id": str(line.pk), "DELETE": "on"}])
        )
        gestion = reverse("facturation_sociale:gestion") + "?mois=4&annee=2026"
        self.assertRedirects(response, gestion, fetch_redirect_response=False)
        self.assertContains(self.client.get(gestion), "Prestations supprimées.")
        self.assertFalse(PrestationSociale.objects.exists())


class SaisieRefonteTests(DonneesFacturationSociale, TestCase):
    """Écran de saisie refondu : le POST doit rester celui d'avant."""

    LIGNE_CHAMPS = [
        "id", "DELETE", "mode_tarification", "mode_cout_prestataire",
        "prestation", "detail", "quantite", "prestataire",
        "tarif_client_personnalise", "motif_tarif_personnalise",
        "cout_prestataire_personnalise", "motif_cout_prestataire_personnalise",
        "deja_facturee",
    ]

    def page(self):
        return self.client.get(f"{self.url}?client={self.client_a.pk}&mois=4&annee=2026")

    def post_like_browser(self, response, token, **changes):
        data = dict(submitted_fields(response))
        data["submission_id"] = token
        data.update(changes)
        return self.client.post(self.url, data)

    def test_page_layout(self):
        self.create_existing()
        response = self.page()
        self.assertContains(response, "Saisie des prestations")
        self.assertContains(response, "Toutes les prestations d'un client pour un mois")
        self.assertContains(response, "Avril 2026")
        self.assertNotContains(response, "nav-tabs")
        self.assertNotContains(response, "None - Alpha")
        self.assertNotContains(response, ">Charger<")
        self.assertContains(response, 'id="save-status"')
        self.assertContains(response, 'aria-label="Tarif et coût de la ligne"')
        self.assertContains(response, 'id="fs-panneau-form-0"')
        self.assertContains(response, 'colspan="9"')
        self.assertContains(response, "Supprimer la ligne")
        self.assertContains(response, 'id="total-reste"')
        self.assertContains(response, "ⓘ au survol : détail d'une exception")
        # Le gabarit des nouvelles lignes contient ligne + panneau.
        self.assertContains(response, 'id="fs-panneau-form-__prefix__"')
        self.assertContains(response, 'name="form-__prefix__-mode_tarification"')

    def test_templates_have_no_overlay(self):
        folder = Path(__file__).parent / "templates" / "facturation_sociale"
        for name in ("prestations_par_client.html", "includes/prestation_ligne.html"):
            source = (folder / name).read_text(encoding="utf-8")
            for forbidden in ("z-index", "position: absolute", "position: fixed",
                              "position:absolute", "position:fixed", "modal",
                              "data-bs-toggle"):
                self.assertNotIn(forbidden, source, f"{forbidden} dans {name}")

    def test_submitted_field_names_are_unchanged(self):
        self.create_existing()
        self.create_existing(detail="Deuxième")
        names = sorted(name for name, _ in submitted_fields(self.page()))
        expected = [
            "annee", "client", "csrfmiddlewaretoken",
            "form-INITIAL_FORMS", "form-MAX_NUM_FORMS", "form-MIN_NUM_FORMS",
            "form-TOTAL_FORMS", "mois", "submission_id",
        ]
        for index in range(2):
            for champ in self.LIGNE_CHAMPS:
                # Une case non cochée n'est pas envoyée, comme avant.
                if champ != "deja_facturee":
                    expected.append(f"form-{index}-{champ}")
        self.assertEqual(names, sorted(expected))

    def test_browser_roundtrip_keeps_historical_snapshots(self):
        line = self.create_existing(
            tarif_personnalise=True,
            tarif_client_applique=Decimal("55.00"),
            motif_tarif_personnalise="Négocié",
        )
        self.prestation.tarif_client_standard = Decimal("99.00")
        self.prestation.save()
        TarifPrestataire.objects.filter(
            prestation=self.prestation, prestataire=self.prestataire
        ).update(cout_unitaire=Decimal("77.00"))

        response = self.page()
        # Le standard affiché est le snapshot historique, pas le tarif actuel.
        self.assertContains(response, 'data-std-client="50.00"')
        self.assertContains(response, 'data-std-cout="20.00"')
        self.assertContains(response, 'data-anomalie-cout="0"')

        result = self.post_like_browser(response, "roundtrip", **{"form-0-quantite": "2.00"})
        self.assertEqual(result.status_code, 302)
        line.refresh_from_db()
        self.assertEqual(line.quantite, Decimal("2.00"))
        self.assertEqual(line.tarif_client_standard_snapshot, Decimal("50.00"))
        self.assertEqual(line.tarif_client_applique, Decimal("55.00"))
        self.assertTrue(line.tarif_personnalise)
        self.assertEqual(line.motif_tarif_personnalise, "Négocié")
        self.assertEqual(line.cout_prestataire_standard_snapshot, Decimal("20.00"))
        self.assertEqual(line.cout_prestataire_unitaire_snapshot, Decimal("20.00"))

    def new_line(self, token, **row):
        response = self.client.post(self.url, self.payload([row], token=token))
        self.assertEqual(response.status_code, 302)
        return PrestationSociale.objects.get()

    def test_new_standard_line(self):
        line = self.new_line("std", detail="Paul", quantite="2.00")
        self.assertEqual(line.tarif_client_standard_snapshot, Decimal("50.00"))
        self.assertEqual(line.tarif_client_applique, Decimal("50.00"))
        self.assertEqual(line.cout_prestataire_unitaire_snapshot, Decimal("20.00"))
        self.assertFalse(line.tarif_personnalise or line.cout_prestataire_personnalise)
        self.assertEqual(line.montant_facture, Decimal("100.00"))

    def test_new_line_with_exceptional_price(self):
        line = self.new_line(
            "prix",
            mode_tarification="personnalise",
            tarif_client_personnalise="45.00",
            motif_tarif_personnalise="Geste commercial",
        )
        self.assertTrue(line.tarif_personnalise)
        self.assertEqual(line.tarif_client_applique, Decimal("45.00"))
        self.assertEqual(line.tarif_client_standard_snapshot, Decimal("50.00"))
        self.assertEqual(line.motif_tarif_personnalise, "Geste commercial")

    def test_new_line_with_exceptional_cost(self):
        line = self.new_line(
            "cout",
            mode_cout_prestataire="personnalise",
            cout_prestataire_personnalise="12.50",
            motif_cout_prestataire_personnalise="Remise",
        )
        self.assertTrue(line.cout_prestataire_personnalise)
        self.assertEqual(line.cout_prestataire_unitaire_snapshot, Decimal("12.50"))
        self.assertEqual(line.cout_prestataire_standard_snapshot, Decimal("20.00"))
        self.assertEqual(line.marge, Decimal("37.50"))

    def test_new_line_already_billed(self):
        self.assertTrue(self.new_line("facturee", deja_facturee="on").deja_facturee)

    def test_browser_roundtrip_deletes_marked_line(self):
        keep = self.create_existing(detail="Garder")
        drop = self.create_existing(detail="Supprimer")
        response = self.page()
        result = self.post_like_browser(response, "suppr", **{"form-1-DELETE": "on"})
        self.assertEqual(result.status_code, 302)
        self.assertEqual(list(PrestationSociale.objects.values_list("pk", flat=True)), [keep.pk])
        self.assertFalse(PrestationSociale.objects.filter(pk=drop.pk).exists())

    def test_panel_opens_on_validation_error(self):
        response = self.client.post(
            self.url,
            self.payload([{}, {"mode_tarification": "personnalise"}], token="err"),
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Indiquez le prix unitaire exceptionnel.", content)
        panneau_0 = content.split('id="fs-panneau-form-0"')[1].split(">")[0]
        panneau_1 = content.split('id="fs-panneau-form-1"')[1].split(">")[0]
        self.assertIn("hidden", panneau_0)
        self.assertNotIn("hidden", panneau_1)
        self.assertEqual(PrestationSociale.objects.count(), 0)

    def test_warns_about_lines_whose_standard_cost_is_missing(self):
        # Lignes créées avant la migration 0002 : coût standard à 0.
        self.create_existing(cout_prestataire_standard_snapshot=Decimal("0.00"))
        response = self.page()
        self.assertContains(response, 'data-anomalie-cout="1"')
        self.assertContains(response, "Enregistrer cette page remplacera leur coût")


class AccesTests(TestCase):
    """Toute l'app est réservée au personnel du cabinet."""

    def urls(self):
        # Parcourt urls.py : une nouvelle URL est vérifiée automatiquement.
        for pattern in fs_urls.urlpatterns:
            kwargs = {"pk": 1} if "<int:pk>" in str(pattern.pattern) else {}
            yield reverse(f"facturation_sociale:{pattern.name}", kwargs=kwargs)

    def user_in_group(self, group):
        user = User.objects.create_user(group.lower())
        user.groups.add(Group.objects.create(name=group))
        return user

    def assert_denied(self, user):
        self.client.force_login(user)
        for url in self.urls():
            for method in (self.client.get, self.client.post):
                with self.subTest(url=url, method=method.__name__):
                    self.assertRedirects(
                        method(url), reverse("access_denied"),
                        fetch_redirect_response=False,
                    )

    def test_anonymous_is_sent_to_login(self):
        for url in self.urls():
            for method in (self.client.get, self.client.post):
                with self.subTest(url=url, method=method.__name__):
                    response = method(url)
                    self.assertEqual(response.status_code, 302)
                    self.assertTrue(response.url.startswith("/login/?next="))

    def test_client_group_is_denied(self):
        self.assert_denied(self.user_in_group("Client"))

    def test_partner_group_is_denied(self):
        self.assert_denied(self.user_in_group("Partenaire"))

    def test_staff_and_superuser_are_accepted(self):
        users = (
            User.objects.create_user("equipe", is_staff=True),
            User.objects.create_user("super", is_superuser=True),
        )
        for user in users:
            self.client.force_login(user)
            for name in ("gestion", "prestations_par_client", "configurations",
                         "prestations", "prestataires", "tarifs_prestataires"):
                with self.subTest(user=user.username, name=name):
                    url = reverse(f"facturation_sociale:{name}")
                    self.assertEqual(self.client.get(url).status_code, 200)
