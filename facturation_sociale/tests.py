from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from dossiers.models import Client

from .models import (
    PrestataireSocial,
    PrestationSociale,
    TarifPrestataire,
    TypePrestation,
)


class PrestationsParClientTests(TestCase):
    def setUp(self):
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

    def test_individual_form_still_creates_a_prestation(self):
        response = self.client.post(
            reverse("facturation_sociale:nouvelle_prestation"),
            {
                "client": self.client_a.pk,
                "prestation": self.prestation.pk,
                "prestataire": self.prestataire.pk,
                "mois": "4",
                "annee": "2026",
                "detail": "Individuelle",
                "quantite": "1.00",
                "mode_tarification": "standard",
                "tarif_client_personnalise": "",
                "motif_tarif_personnalise": "",
                "mode_cout_prestataire": "standard",
                "cout_prestataire_personnalise": "",
                "motif_cout_prestataire_personnalise": "",
            },
        )
        self.assertRedirects(response, reverse("facturation_sociale:nouvelle_prestation"))
        self.assertEqual(PrestationSociale.objects.count(), 1)

    def individual_payload(self, **overrides):
        data = {
            "client": self.client_a.pk,
            "prestation": self.prestation.pk,
            "prestataire": self.prestataire.pk,
            "mois": "4",
            "annee": "2026",
            "detail": "",
            "quantite": "1.00",
            "mode_tarification": "standard",
            "tarif_client_personnalise": "",
            "motif_tarif_personnalise": "",
            "mode_cout_prestataire": "standard",
            "cout_prestataire_personnalise": "",
            "motif_cout_prestataire_personnalise": "",
        }
        data.update(overrides)
        return data

    def test_existing_prestations_are_not_already_billed_by_default(self):
        line = self.create_existing()
        line.refresh_from_db()
        self.assertFalse(line.deja_facturee)

    def test_new_prestation_can_be_marked_as_already_billed(self):
        self.client.post(
            reverse("facturation_sociale:nouvelle_prestation"),
            self.individual_payload(deja_facturee="on"),
        )
        self.assertTrue(PrestationSociale.objects.get().deja_facturee)

    def test_editing_a_billed_prestation_keeps_the_flag(self):
        line = self.create_existing(deja_facturee=True)
        url = reverse("facturation_sociale:modifier_prestation_sociale", args=[line.pk])

        # On renvoie exactement ce que la page d'édition pré-remplit.
        response = self.client.get(url)
        self.assertContains(response, "Cette prestation a déjà été facturée.")
        form = response.context["form"]
        self.assertIn("checked", str(form["deja_facturee"]))
        data = {
            name: form[name].value()
            for name in form.fields
            if form[name].value() not in (None, False)
        }
        data["detail"] = "Corrigé"

        self.assertEqual(self.client.post(url, data).status_code, 302)
        line.refresh_from_db()
        self.assertEqual(line.detail, "Corrigé")
        self.assertTrue(line.deja_facturee)

    def test_editing_can_uncheck_the_flag(self):
        line = self.create_existing(deja_facturee=True)
        url = reverse("facturation_sociale:modifier_prestation_sociale", args=[line.pk])
        self.client.post(url, self.individual_payload())
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
        for name in ("modifier_prestation_sociale", "supprimer_prestation_sociale"):
            self.assertNotContains(
                response, reverse(f"facturation_sociale:{name}", args=[line.pk])
            )
