import csv
from django.core.management.base import BaseCommand
from dossiers.models import Client

class Command(BaseCommand):
    help = "Importe la périodicité de la saisie depuis un CSV"

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help="Chemin du fichier CSV")

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']

        with open(csv_file, newline='', encoding='latin-1') as f:
            reader = csv.DictReader(f)

            for row in reader:
                numero = row.get('numero')
                periodicite = row.get('periodicite')

                if not numero or not periodicite:
                    self.stdout.write(self.style.WARNING(f"Ligne ignorée : {row}"))
                    continue

                try:
                    client = Client.objects.get(numero=numero)
                    client.periodicite = periodicite
                    client.save()
                    self.stdout.write(self.style.SUCCESS(f"✔ Client {numero} mis à jour"))
                except Client.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"✘ Client {numero} introuvable"))