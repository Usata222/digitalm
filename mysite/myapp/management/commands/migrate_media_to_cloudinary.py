# [NEW FILE] — myapp/management/commands/migrate_media_to_cloudinary.py
#
# WHY THIS EXISTS:
# Your existing Product records have `thumbnail` and `image` fields
# pointing to LOCAL paths (e.g. "thumbnails/Untitled.jpg") that were
# saved back when DEFAULT_FILE_STORAGE was local disk. After switching
# DEFAULT_FILE_STORAGE to Cloudinary, those paths still point to local
# files that:
#   1. don't exist on Render (ephemeral filesystem), AND
#   2. were never uploaded to Cloudinary, so {{ product.thumbnail.url }}
#      resolves to nothing / a broken Cloudinary URL.
#
# This command reads each Product's local file from your project's
# media/ folder (present in this zip), uploads it to Cloudinary, and
# updates the DB field to the new Cloudinary path.
#
# USAGE (run locally, where the media/ files exist, with .env containing
# REAL Cloudinary credentials):
#   python manage.py migrate_media_to_cloudinary
#
# Run this ONCE. After this, your db.sqlite3 references Cloudinary-hosted
# files. Push the updated db.sqlite3 to Render afterwards so the live site
# has the same references.

import os
from django.core.management.base import BaseCommand
from django.conf import settings
from myapp.models import Product
import cloudinary.uploader


class Command(BaseCommand):
    help = "Uploads existing local media files (thumbnails/images) to Cloudinary and updates Product records."

    def handle(self, *args, **options):
        products = Product.objects.all()
        total = products.count()
        self.stdout.write(f"Found {total} product(s).")

        for product in products:
            self._migrate_field(product, "thumbnail")
            self._migrate_field(product, "image")

        self.stdout.write(self.style.SUCCESS("Done. Re-check thumbnails on your site."))

    def _migrate_field(self, product, field_name):
        field_file = getattr(product, field_name)

        if not field_file:
            return

        relative_path = field_file.name
        local_path = os.path.join(settings.BASE_DIR, "media", relative_path)

        if not os.path.exists(local_path):
            self.stdout.write(
                self.style.WARNING(
                    f"  [SKIP] Product #{product.id} '{product.name}' "
                    f"{field_name}: local file not found at {local_path} "
                    f"(may already be migrated, or file is missing)."
                )
            )
            return

        try:
            result = cloudinary.uploader.upload(
                local_path,
                folder=os.path.dirname(relative_path) or None,
                use_filename=True,
                unique_filename=True,
                overwrite=False,
                resource_type="image",
            )
            public_id = result.get("public_id")
            format_ext = result.get("format")
            new_name = f"{public_id}.{format_ext}" if format_ext else public_id

            setattr(product, field_name, new_name)
            product.save(update_fields=[field_name])

            self.stdout.write(
                self.style.SUCCESS(
                    f"  [OK] Product #{product.id} '{product.name}' "
                    f"{field_name}: {relative_path} -> {new_name}"
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"  [ERROR] Product #{product.id} '{product.name}' "
                    f"{field_name}: {e}"
                )
            )
