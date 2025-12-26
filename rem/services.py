import os
import json

from django.conf import settings
from django.db import connection

from rem.etl import procesar_archivo_con_mapeo

# Cache en memoria para no consultar la BD a cada fila
COLUMN_TYPES_CACHE = {}


def get_column_types(tabla_bd: str) -> dict:
    """
    Devuelve un dict {nombre_columna: data_type} para la tabla dada,
    usando information_schema.columns. Resultado cacheado.
    """
    if tabla_bd in COLUMN_TYPES_CACHE:
        return COLUMN_TYPES_CACHE[tabla_bd]

    # tabla_bd viene como "cesfam_raw.rem_a01_seccion_a"
    if "." in tabla_bd:
        schema_name, table_name = tabla_bd.split(".", 1)
    else:
        schema_name = "public"
        table_name = tabla_bd

    sql = """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = %s
          AND table_name   = %s
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [schema_name, table_name])
        rows = cursor.fetchall()

    col_types = {name: dtype for (name, dtype) in rows}
    COLUMN_TYPES_CACHE[tabla_bd] = col_types
    return col_types


def cast_value_for_column(value, col_type: str):
    """
    Convierte 'value' a un tipo compatible con 'col_type' de PostgreSQL.
    - Para columnas NUMERIC/INTEGER: intenta convertir, si no puede → None.
    - Para TEXT/VARCHAR: lo deja como string.
    - Otros tipos: devuelve el valor tal cual.
    """
    if value is None:
        return None

    # Normalizamos type
    col_type = (col_type or "").lower()

    # Texto
    if "char" in col_type or col_type in ("text",):
        return str(value).strip()

    # Enteros
    if col_type in ("integer", "bigint", "smallint"):
        try:
            return int(value)
        except Exception:
            try:
                # Por si viene como "12.0" o "12,0"
                s = str(value).replace(",", ".")
                return int(float(s))
            except Exception:
                return None

    # Numéricos con decimales
    if col_type.startswith("numeric") or col_type in ("real", "double precision"):
        try:
            s = str(value).replace(",", ".")
            return float(s)
        except Exception:
            return None

    # Por defecto, no tocamos
    return value


def insertar_fila_raw(tabla_bd: str, fila: dict):
    """
    Inserta UNA fila en la tabla RAW correspondiente (cesfam_raw.rem_xxx_seccion_xxx),
    pero:
      - Solo usa columnas que realmente existen en la tabla.
      - Castea los valores según el tipo real de la columna.
      - Si un valor no calza con el tipo (ej: 'Ambos Sexos' en NUMERIC) → None.
    """
    col_types = get_column_types(tabla_bd)

    columnas = []
    placeholders = []
    params = []

    for key, value in fila.items():
        # Estos son metadatos, no columnas reales
        if key in ("hoja", "seccion", "fila"):
            continue

        # Si la columna no existe en la tabla, la ignoramos
        if key not in col_types:
            # Opcional: podrías loguear si quieres depurar:
            # print(f"⚠ Columna {key} no existe en {tabla_bd}, se omite")
            continue

        col_type = col_types[key]
        columnas.append(key)
        placeholders.append("%s")
        params.append(cast_value_for_column(value, col_type))

    if not columnas:
        # No hay nada que insertar (todas columnas desconocidas)
        return

    columnas_sql = ", ".join(columnas)
    placeholders_sql = ", ".join(placeholders)

    sql = f"""
        INSERT INTO {tabla_bd} ({columnas_sql})
        VALUES ({placeholders_sql})
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, params)


def obtener_tabla_bd(rem: str, seccion: str, estructuras: dict):
    """
    Busca en rem_structures.json cuál es la tabla correspondiente
    a (rem, seccion).
    """
    rem = rem.lower()
    seccion = seccion.upper()

    if rem not in estructuras:
        return None

    if seccion not in estructuras[rem]:
        return None

    return estructuras[rem][seccion]["tabla_bd"]


def procesar_y_guardar(nombre_archivo: str):
    """
    1. Corre el ETL sobre el Excel consolidado.
    2. Inserta cada fila en la tabla RAW correspondiente.
    3. Devuelve un resumen.
    """
    ruta_excel = os.path.join(settings.MEDIA_ROOT, "rem_uploads", nombre_archivo)

    if not os.path.exists(ruta_excel):
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_excel}")

    # 1) Ejecutar ETL (leer Excel + mapeo)
    registros = procesar_archivo_con_mapeo(ruta_excel)

    # 2) Cargar estructura maestro (tablas y columnas reales)
    ruta_maestro = os.path.join(settings.BASE_DIR, "rem", "rem_structures.json")
    with open(ruta_maestro, "r", encoding="utf-8") as f:
        estructuras = json.load(f)

    resumen = {}

    # 3) Insertar cada registro
    for reg in registros:
        rem = reg["hoja"]        # ej: A01
        seccion = reg["seccion"] # ej: A.1 o B

        tabla = obtener_tabla_bd(rem, seccion, estructuras)
        if not tabla:
            # Sección que aún no modelamos como tabla RAW
            print(f"⚠ No existe tabla RAW para {rem}-{seccion}")
            continue

        # Construir fila limpia con nombre de columna SQL correcto
        fila_sql = {"fila_excel": reg["fila"]}

        for key, value in reg.items():
            if key in ("hoja", "seccion", "fila"):
                continue
            fila_sql[key] = value

        # Inserta respetando tipos de BD
        insertar_fila_raw(tabla, fila_sql)

        resumen[(rem, seccion)] = resumen.get((rem, seccion), 0) + 1

    return registros, resumen
