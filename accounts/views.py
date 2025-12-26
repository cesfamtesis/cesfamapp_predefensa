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

        Seguridad:
        - Aquí solo se valida el primer factor.
        - El acceso al sistema queda bloqueado hasta validar 2FA.
        - TwoFAMiddleware controla el acceso vía sesión.
        """
        user = form.get_user()

        # 1) Login estándar (primer factor)
        login(self.request, user)

        # 2) Marcar sesión como NO verificada en 2FA
        self.request.session["twofa_verified"] = False

        # 3) Enviar código 2FA (no bloqueante)
        enviar_codigo_2fa(user)

        # 4) Redirigir a verificación 2FA
        return redirect("accounts:verificar_2fa")


# ============================================================
# LOGOUT CON AUDITORÍA
# ============================================================

@login_required
def logout_view(request):
    """
    Cierra sesión y registra auditoría.
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
    Genera un código 2FA, lo guarda en BD y lo envía por correo.

    IMPORTANTE:
    - El envío de correo NO debe romper el login.
    - Se maneja con tolerancia a fallos (Render-safe).
    """
    codigo = f"{random.randint(100000, 999999)}"

    TwoFactorCode.objects.create(
        user=user,
        code=codigo,
    )

    # Logs de apoyo (desarrollo / demo)
    print("===================================")
    print("✅ Código 2FA generado:", codigo)
    print("📧 Enviando correo a:", user.email)
    print("===================================")

    subject = "Código de verificación - Sistema REM CESFAM"

    context = {
        "user": user,
        "codigo": codigo,
        "minutos": TWO_FA_EXPIRATION_MINUTES,
    }

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

    # 🔐 ENVÍO SEGURO (NO BLOQUEANTE)
    try:
        email.send(fail_silently=True)
    except Exception as e:
        # Nunca debe romper el flujo de login
        print("❌ Error enviando correo 2FA:", str(e))


# ============================================================
# VERIFICACIÓN DEL CÓDIGO 2FA
# ============================================================

@login_required
def verificar_2fa(request):
    """
    Valida el código 2FA ingresado por el usuario.
    """

    # --------------------------------------------
    # REENVIAR CÓDIGO
    # --------------------------------------------
    if request.method == "POST" and "generar_nuevo_codigo" in request.POST:
        enviar_codigo_2fa(request.user)
        messages.info(
            request,
            "Se ha enviado un nuevo código de verificación a tu correo."
        )
        return redirect("accounts:verificar_2fa")

    # --------------------------------------------
    # VALIDAR CÓDIGO INGRESADO
    # --------------------------------------------
    if request.method == "POST":
        codigo = (request.POST.get("codigo") or "").strip()

        if not codigo:
            messages.error(request, "Debes ingresar el código de verificación.")
            return redirect("accounts:verificar_2fa")

        registro = TwoFactorCode.objects.filter(
            user=request.user,
            code=codigo,
            is_used=False,
        ).first()

        if registro:
            expiracion = registro.created_at + timedelta(
                minutes=TWO_FA_EXPIRATION_MINUTES
            )

            if timezone.now() > expiracion:
                messages.error(
                    request,
                    "El código ha expirado. Solicita uno nuevo."
                )
                return redirect("accounts:verificar_2fa")

            # Código válido
            registro.is_used = True
            registro.save()

            # Marcar sesión como verificada
            request.session["twofa_verified"] = True

            # Auditoría de login completo
            registrar_auditoria(
                request,
                AuditLog.ACCION_LOGIN,
                f"Ingreso exitoso al sistema (2FA validado) del usuario {request.user.username}",
            )

            return redirect("home")

        messages.error(request, "Código incorrecto.")

    # GET o error
    return render(request, "verificar_2fa.html")
