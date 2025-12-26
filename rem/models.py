from django.db import models
from django.conf import settings


# ===============================================================
# DIMENSION PERIODO  (ya existe en PostgreSQL → managed=False)
# ===============================================================
class DimPeriodo(models.Model):
    id_periodo = models.IntegerField(primary_key=True)
    anio = models.IntegerField()
    mes = models.IntegerField()
    descripcion = models.TextField(null=True, blank=True)
    creado_en = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'cesfam_core"."dim_periodo'   # schema + tabla real

    def __str__(self):
        base = f"{self.anio}-{self.mes:02d}"
        if self.descripcion:
            return f"{base} ({self.descripcion})"
        return base


# ===============================================================
# ARCHIVO REM SUBIDO POR EL USUARIO
# ===============================================================
class ArchivoREM(models.Model):
    id_archivo = models.BigAutoField(primary_key=True)

    # nombre original del archivo subido
    nombre_original = models.CharField(max_length=255)

    # archivo guardado en /media/rem_uploads/
    archivo = models.FileField(upload_to='rem_uploads/')

    # 🔥 FK REAL a DimPeriodo (OBLIGATORIO para Módulo 3 + ETL CORE)
    periodo = models.ForeignKey(
        DimPeriodo,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="archivos"
    )

    # fecha en que se subió el archivo
    fecha_carga = models.DateTimeField(auto_now_add=True)

    # si ya se procesó y se llenó registro_rem
    procesado = models.BooleanField(default=False)

    # 👉 nuevo: para “eliminar” sin borrar físicamente
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'archivo_rem'

    def __str__(self):
        return f"{self.nombre_original} ({self.periodo})"


# ===============================================================
# REGISTROS GENERADOS POR EL ETL → JSON
# ===============================================================
class RegistroREM(models.Model):
    id_registro = models.BigAutoField(primary_key=True)

    archivo = models.ForeignKey(
        ArchivoREM,
        on_delete=models.CASCADE,
        related_name="registros"
    )

    hoja = models.CharField(max_length=10)      # A01, A02, A11, A11A...
    seccion = models.CharField(max_length=20)   # A, B, A.1, C.2, H.3, etc.
    fila = models.IntegerField(default=0)       # número interno en la sección

    # JSON con campos mapeados → valores reales del Excel
    datos = models.JSONField()

    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'registro_rem'

    def __str__(self):
        return f"{self.archivo.nombre_original} [{self.hoja}-{self.seccion}] fila {self.fila}"

class AuditLog(models.Model):
    ACCION_LOGIN = "LOGIN"
    ACCION_LOGOUT = "LOGOUT"
    ACCION_UPLOAD = "UPLOAD_REM"
    ACCION_PROCESAR = "PROCESAR_REM"
    ACCION_PERIODO = "CRUD_PERIODO"
    ACCION_OTRA = "OTRA"

    ACCIONES_CHOICES = [
        (ACCION_LOGIN, "Inicio de sesión"),
        (ACCION_LOGOUT, "Cierre de sesión"),
        (ACCION_UPLOAD, "Subida de archivo REM"),
        (ACCION_PROCESAR, "Procesamiento de archivo REM"),
        (ACCION_PERIODO, "Gestión de períodos"),
        (ACCION_OTRA, "Otro"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    accion = models.CharField(max_length=50, choices=ACCIONES_CHOICES)
    descripcion = models.TextField()
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_log"
        ordering = ["-fecha_hora"]

    def __str__(self):
        u = self.usuario.username if self.usuario else "Anon"
        return f"[{self.fecha_hora}] {u} - {self.accion}"

class BackupLog(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    archivo = models.CharField(max_length=255)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.archivo} - {self.fecha}"