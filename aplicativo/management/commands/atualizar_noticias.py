from django.core.management.base import BaseCommand
from ...services.atualizar_noticias_job import atualizar_noticias_job

class Command(BaseCommand):
    help = "Busca RSS e atualiza notícias no banco"

    def handle(self, *args, **options):
        novas = atualizar_noticias_job()
        self.stdout.write(self.style.SUCCESS(f"OK - novas: {novas}"))
