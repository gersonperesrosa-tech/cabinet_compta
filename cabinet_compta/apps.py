from django.apps import AppConfig

class CabinetComptaConfig(AppConfig):
    name = 'cabinet_compta'

    def ready(self):
        import cabinet_compta.signals
