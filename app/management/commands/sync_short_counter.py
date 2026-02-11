from django.core.management.base import BaseCommand
from app.utils.id_generator import initialize_counter

class Command(BaseCommand):
    help = "Sync Redis short_url_counter with database"
    def handle(self, *args,**kwargs):
        Value=initialize_counter()
        self.stdout.write(self.style.SUCCESS(f"Counter synchronized to {Value}"))