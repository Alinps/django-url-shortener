from django.core.management.base import BaseCommand
from django.db import transaction

from app.models import ShortURL, ShortURLCore, ShortURLMeta

class Command(BaseCommand):
    help = "Backfill ShortURL data into ShortURLCore and ShortURLMeta"

    def handle(self, *args, **options):
        self.stdout.write("Starting backfill process...")

        created_core = 0
        created_meta = 0
        skipped = 0

        # Use iterator to avoid loading everything into memory
        for old in ShortURL.objects.all().iterator():

            # SAFETY CHECK: avoid duplicates if command is re-rum
            if ShortURLCore.objects.filter(short_code=old.short_code).exists():
                skipped += 1
                continue

            with transaction.atomic():

                # Create HOT record
                core = ShortURLCore.objects.create(
                    short_code=old.short_code,
                    original_url=old.original_url,
                    is_active=old.is_active,
                    created_at=old.created_at
                )
                created_core += 1

                # Create COLD record
                ShortURLMeta.objects.create(
                    short_url=core,
                    user=old.user,
                    title=old.title or "",
                    click_count=old.click_count
                )
                created_meta += 1

        self.stdout.write(self.style.SUCCESS("Backfill completed"))
        self.stdout.write(f"Created ShortURLCore rows: {created_core}")
        self.stdout.write(f"Created ShortURLMeta rows: {created_meta}")
        self.stdout.write(f"Skipped (already exists): {skipped}")