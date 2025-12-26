import os
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.core.management import call_command
from django.shortcuts import render, redirect
from django.contrib import messages

from rem.models import BackupLog


def es_admin(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(es_admin)
def backup_view(request):
    backup_dir = os.path.join(settings.BASE_DIR, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    # ==========================
    # Listar archivos existentes
    # ==========================
    archivos = []
    for f in os.listdir(backup_dir):
        ruta = os.path.join(backup_dir, f)
        if os.path.isfile(ruta):
            archivos.append({
                "nombre": f,
                "tamano": round(os.path.getsize(ruta) / 1024 / 1024, 2)
            })

    # ==========================
    # Ejecutar respaldo manual
    # ==========================
    if request.method == "POST":
        try:
            # Intenta ejecutar el comando de respaldo
            call_command("backup_db")

            ultimo = sorted(os.listdir(backup_dir))[-1]

            BackupLog.objects.create(
                archivo=ultimo,
                usuario=request.user
            )

            messages.success(
                request,
                "Respaldo generado correctamente."
            )

        except Exception as e:
            # En Render u otros entornos cloud el respaldo no está disponible
            messages.warning(
                request,
                "El respaldo no está disponible en este entorno de despliegue."
            )

        return redirect("backup_view")

    # ==========================
    # Historial de respaldos
    # ==========================
    logs = BackupLog.objects.order_by("-fecha")

    return render(request, "backups/backup.html", {
        "archivos": archivos,
        "logs": logs
    })
