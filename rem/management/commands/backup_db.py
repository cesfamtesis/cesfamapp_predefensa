import os
import subprocess
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Genera un respaldo lógico de la base de datos PostgreSQL"

    def handle(self, *args, **options):
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_dir = os.path.join(settings.BASE_DIR, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        db = settings.DATABASES["default"]

        backup_file = os.path.join(
            backup_dir,
            f"backup_{db['NAME']}_{fecha}.dump"
        )

        # 👉 RUTA EXPLÍCITA A pg_dump (Windows)
        PG_DUMP = r"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe"

        command = [
            PG_DUMP,
            "-h", db.get("HOST", "localhost"),
            "-p", str(db.get("PORT", "5432")),
            "-U", db["USER"],
            "-F", "c",
            "-f", backup_file,
            db["NAME"],
        ]

        env = os.environ.copy()
        env["PGPASSWORD"] = db["PASSWORD"]

        subprocess.run(command, env=env, check=True)

        self.stdout.write(
            self.style.SUCCESS(f"✔️ Respaldo generado: {backup_file}")
        )
