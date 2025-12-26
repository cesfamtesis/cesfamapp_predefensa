from django.urls import path
from django.contrib.auth.decorators import user_passes_test
from . import views
from rem.views_backup import backup_view


def es_admin(user):
    """
    Retorna True solo si el usuario es administrador del sistema
    (is_staff o is_superuser).
    """
    return user.is_staff or user.is_superuser


urlpatterns = [
    # ===== HOME =====
    # raíz del sistema → home.html
    path('', views.home, name='home'),               # /

    # (opcional) que /home/ también muestre el home
    path('home/', views.home, name='home_alt'),      # /home/

    # ===== PERÍODOS (CRUD) =====
    path('periodos/', views.lista_periodos, name='lista_periodos'),    # /periodos/

    path('periodos/nuevo/', views.crear_periodo, name='crear_periodo'),

    path(
        'periodos/<int:id_periodo>/editar/',
        views.editar_periodo,
        name='editar_periodo'
    ),

    path(
        'periodos/<int:id_periodo>/eliminar/',
        views.eliminar_periodo,
        name='eliminar_periodo'
    ),

    path(
        'periodos/<int:id_periodo>/reactivar/',
        views.reactivar_periodo,
        name='reactivar_periodo'
    ),

    # ===== ARCHIVOS REM =====
    path('subir/', views.subir_excel, name='subir_excel'),             # /subir/

    path('archivos/', views.lista_archivos, name='lista_archivos'),    # /archivos/

    path(
        'archivo/<int:archivo_id>/procesar/',
        views.procesar_archivo_generico,
        name='procesar_archivo_generico'
    ),

    path(
        'archivo/<int:archivo_id>/registros/',
        views.ver_registros_archivo,
        name='ver_registros_archivo'
    ),

    path(
        'archivo/<int:archivo_id>/desactivar/',
        views.desactivar_archivo,
        name='desactivar_archivo'
    ),

    # ===== BITÁCORA / AUDITORÍA (solo admin/staff) =====
    path(
        "auditoria/",
        user_passes_test(es_admin)(views.lista_auditoria),
        name="lista_auditoria",
    ),

    # ===== INGRESO MANUAL DE REM POR PERÍODO =====
    # 1) Pantalla SOLO de REM
    path(
        "periodos/<int:periodo_id>/rem/",
        views.seleccionar_rem_periodo,
        name="seleccionar_rem_periodo",
    ),

    # 2) Pantalla de SECCIONES de un REM
    path(
        "periodos/<int:periodo_id>/rem/<str:hoja>/secciones/",
        views.seleccionar_seccion_periodo,
        name="seleccionar_seccion_periodo",
    ),

    # 3) Formulario final (ya lo tenías igual)
    path(
        "periodos/<int:periodo_id>/rem/<str:hoja>/<str:seccion>/nuevo/",
        views.ingresar_registro_manual_periodo,
        name="ingresar_registro_manual_periodo",
    ),

    path(
        "periodos/<int:periodo_id>/rem/ver/",
        views.ver_datos_rem_periodo,
        name="ver_datos_rem_periodo",
    ),

    path(
        'periodos/<int:periodo_id>/rem/<str:hoja>/<str:seccion>/',
        views.ver_detalle_rem,
        name='ver_detalle_rem'
    ),

    # ===== REPORTES =====
    path("reportes/", views.reportes_home, name="reportes_home"),
    path(
        "reportes/a01/seccion-a/<int:periodo_id>/",
        views.reporte_a01_seccion_a,
        name="reporte_a01_seccion_a",
    ),
    path(
    "periodos/<int:periodo_id>/reporte/a01/seccion-a/excel/",
    views.exportar_a01_seccion_a_excel,
    name="exportar_a01_seccion_a_excel",
        ),
    path(
        "periodos/<int:periodo_id>/reporte/a01/seccion-a/pdf/",
        views.exportar_a01_seccion_a_pdf,
         name="exportar_a01_seccion_a_pdf",
    ),
    path("backups/", backup_view, name="backup_view"),
]
