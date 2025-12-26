from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


# ============================================================
# Decorator: exige que el usuario tenga 2FA validado
# - Se basa en request.session["twofa_verified"] que tú ya usas.
# ============================================================
def twofa_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        # Si no está logueado, Django lo mandará al login con @login_required
        # (por eso normalmente se usa junto con @login_required)
        if not request.session.get("twofa_verified", False):
            messages.warning(request, "Debes validar el código de verificación para continuar.")
            return redirect("accounts:verificar_2fa")
        return view_func(request, *args, **kwargs)
    return _wrapped


# ============================================================
# Helpers de roles
# ============================================================
def is_admin_user(user) -> bool:
    """
    Define quién es 'Administrador' para tu sistema.
    Reglas:
    - Superuser siempre es admin.
    - O pertenece al grupo 'Administradores'.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name="Administradores").exists()


# ============================================================
# Decorator: exige rol administrador
# ============================================================
def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not is_admin_user(request.user):
            messages.error(request, "Acceso denegado. Se requiere rol Administrador.")
            return redirect("home")  # o a donde tú prefieras
        return view_func(request, *args, **kwargs)
    return _wrapped
