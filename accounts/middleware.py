from django.shortcuts import redirect
from django.urls import reverse


class TwoFAMiddleware:
    """
    Middleware de seguridad para forzar la validación del segundo factor (2FA).

    Regla:
    - Si el usuario está autenticado pero NO ha validado el 2FA,
      no puede acceder a ningún módulo del sistema.
    - Solo se permite el acceso a:
        * pantalla de verificación 2FA
        * logout
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo aplicamos el control si el usuario ya pasó usuario/contraseña
        if request.user.is_authenticated:
            twofa_ok = request.session.get("twofa_verified", False)

            # Rutas que pueden visitarse sin 2FA validado
            rutas_permitidas = [
                reverse("accounts:verificar_2fa"),
                reverse("accounts:logout"),
            ]

            # Si no ha validado el 2FA y trata de acceder a otra ruta → bloqueo
            if not twofa_ok and request.path not in rutas_permitidas:
                return redirect("accounts:verificar_2fa")

        return self.get_response(request)
