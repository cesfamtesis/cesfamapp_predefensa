# rem/auditoria.py
from .models import AuditLog


def _obtener_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def registrar_auditoria(request, accion, descripcion):
    """
    Registra una acción en la bitácora de auditoría, asociada al usuario
    (si está autenticado), IP y user agent.
    """
    usuario = request.user if request.user.is_authenticated else None
    ip = _obtener_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "")

    AuditLog.objects.create(
        usuario=usuario,
        accion=accion,
        descripcion=descripcion,
        ip=ip,
        user_agent=user_agent,
    )
