# accounts/urls.py
from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views


app_name = "accounts"

urlpatterns = [
    # =====================================
    # Login personalizado
    # =====================================
    path(
        "login/",
        views.CustomLoginView.as_view(),
        name="login"
    ),

    # =====================================
    # Logout personalizado con auditoría
    # =====================================
    path(
        "logout/",
        views.logout_view,
        name="logout"
    ),

    # =====================================
    # Recuperación de contraseña
    # =====================================

    # 1) Formulario para ingresar el correo
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="password_reset_form.html",
            subject_template_name="password_reset_subject.txt",
            email_template_name="password_reset_email.txt",        # versión texto
            html_email_template_name="password_reset_email.html",  # versión HTML
            success_url=reverse_lazy("accounts:password_reset_done"),
        ),
        name="password_reset",
    ),

    # 2) Mensaje de "Te enviamos un correo"
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="password_reset_done.html"
        ),
        name="password_reset_done",
    ),

    # 3) Formulario donde el usuario escribe nueva contraseña
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="password_reset_confirm.html",
            success_url=reverse_lazy("accounts:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),

    # 4) Pantalla de confirmación "Tu contraseña fue cambiada"
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path("verificar-2fa/", views.verificar_2fa, name="verificar_2fa"),
]
