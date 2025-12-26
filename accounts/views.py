from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone

import random
from datetime import timedelta

from rem.auditoria import registrar_auditoria
from rem.models import AuditLog
from .models import TwoFactorCode


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

# Tiempo de validez del código 2FA (en minutos)
TWO_FA_EXPIRATION_MINUTES = 2


# ============================================================
# LOGIN PERSONALIZADO + SEGUNDO FACTOR (2FA)
# ============================================================

class CustomLoginView(LoginView):
    template_name = "login.html"

    def form_valid(self, form):
        """
        Se ejecuta cuando el login (usuario/contraseña) es válido.

        IMPORTANTE (seguridad):
        - Aquí solo se valida el primer factor (credenciales).
        - El acceso a módulos del sistema queda bloqueado hasta validar 2FA.
        - El middleware TwoFAMiddleware controla ese bloqueo vía sesión.
        """
        user = form.get_user()

        # 1) Inicio de sesión estándar (primer factor)
        login(self.request, user)

        # 2) Marcar que el usuario aún NO ha verificado el segundo factor
        self.request.session["twofa_verified"] = False

        # 3) Envío del código 2FA al correo
        enviar_codigo_2fa(user)

        # 4) Redirección a pantalla de verificación
        return redirect("accounts:verificar_2fa")


# ============================================================
# LOGOUT CON REGISTRO DE AUDITORÍA
# ============================================================

@login_required
def logout_view(request):
    """
    Cierra sesión y registra el evento en auditoría.
    """
    registrar_auditoria(
        request,
        AuditLog.ACCION_LOGOUT,
        f"Cierre de sesión del usuario {request.user.username}",
    )

    logout(request)
    return redirect("accounts:login")


# ============================================================
# ENVÍO DE CÓDIGO 2FA (CORREO ELECTRÓNICO)
# ============================================================

def enviar_codigo_2fa(user):
    """
    Genera un código 2FA de 6 dígitos, lo guarda en BD y lo envía por correo.
    """
    codigo = f"{random.randint(100000, 999999)}"

    TwoFactorCode.objects.create(
        user=user,
        code=codigo,
    )

    # Logs de apoyo (solo desarrollo)
    print("===================================")
    print("✅ Código 2FA generado:", codigo)
    print("📧 Enviando correo a:", user.email)
    print("===================================")

    subject = "Código de verificación - Sistema REM CESFAM"

    context = {"user": user, "codigo": codigo}

    html_content = render_to_string("emails/codigo_2fa.html", context)

    text_content = strip_tags(
        f"Hola {user.first_name or user.username},\n\n"
        f"Tu código de verificación para el Sistema REM CESFAM es: {codigo}\n"
        f"Este código es válido por {TWO_FA_EXPIRATION_MINUTES} minutos.\n\n"
        "Si tú no solicitaste este código, puedes ignorar este mensaje."
    )

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email="cesfamtesis@gmail.com",
        to=[user.email],
    )
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)


# ============================================================
# VERIFICACIÓN DEL CÓDIGO 2FA
# ============================================================

@login_required
def verificar_2fa(request):
    """
    Vista encargada de validar el código 2FA.
    """

    # --------------------------------------------
    # REENVIAR CÓDIGO 2FA
    # --------------------------------------------
    if request.method == "POST" and "generar_nuevo_codigo" in request.POST:
        enviar_codigo_2fa(request.user)
        messages.info(request, "Se ha enviado un nuevo código de verificación a tu correo.")
        return redirect("accounts:verificar_2fa")

    # --------------------------------------------
    # VALIDACIÓN DEL CÓDIGO INGRESADO
    # --------------------------------------------
    if request.method == "POST":
        codigo = (request.POST.get("codigo") or "").strip()

        if not codigo:
            messages.error(request, "Debes ingresar el código de verificación.")
            return redirect("accounts:verificar_2fa")

        registro = TwoFactorCode.objects.filter(
            user=request.user,
            code=codigo,
            is_used=False
        ).first()

        if registro:
            expiracion = registro.created_at + timedelta(minutes=TWO_FA_EXPIRATION_MINUTES)

            if timezone.now() > expiracion:
                messages.error(request, "El código ha expirado. Solicita uno nuevo.")
                return redirect("accounts:verificar_2fa")

            # Código válido → marcar como usado
            registro.is_used = True
            registro.save()

            # Marcar la sesión como verificada
            request.session["twofa_verified"] = True

            # ✅ AUDITORÍA: INGRESO REAL AL SISTEMA (LOGIN + 2FA)
            registrar_auditoria(
                request,
                AuditLog.ACCION_LOGIN,
                f"Ingreso exitoso al sistema (2FA validado) del usuario {request.user.username}",
            )

            return redirect("home")

        messages.error(request, "Código incorrecto.")

    # GET o error
    return render(request, "verificar_2fa.html")
