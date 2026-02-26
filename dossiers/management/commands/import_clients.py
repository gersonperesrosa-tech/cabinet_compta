import csv
from django.core.management.base import BaseCommand
from dossiers.models import Client

class Command(BaseCommand):
    help = "Importe une base clients depuis un fichier CSV"

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Chemin vers le fichier CSV')

    def handle(self, *args, **options):
        csv_file = options['csv_file']

        # Encodage Windows-friendly
        with open(csv_file, newline='', encoding='latin-1') as f:
            reader = csv.DictReader(f)

            imported = 0
            skipped = 0

            for row in reader:
                # Lecture du numéro client depuis la colonne CSV "numero_client"
                numero = row.get('numero_client', '').strip()

                if not numero:
                    skipped += 1
                    continue

                # Conversion sécurisée du jour d'échéance TVA
                jour_echeance = row.get('jour_echeance_tva', '').strip()
                jour_echeance = int(jour_echeance) if jour_echeance.isdigit() else None

                client, created = Client.objects.get_or_create(
                    numero=numero,
                    defaults={
                        'nom': row.get('nom_client', '').strip(),
                        'forme_juridique': row.get('forme_juridique', '').strip(),
                        'date_cloture': row.get('date_cloture', '').strip(),
                        'regime_tva': row.get('regime_tva', '').strip(),
                        'jour_echeance_tva': jour_echeance,
                        'regime_imposition': row.get('regime_imposition', '').strip(),
                    }
                )

                if created:
                    imported += 1
                else:
                    skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f"Import terminé : {imported} clients créés, {skipped} ignorés."
        ))