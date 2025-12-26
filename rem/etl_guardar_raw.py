import sys
import os

# ================================
# Configurar Django manualmente
# ================================

# Ruta base del archivo actual: .../cesfam_app/rem/etl_guardar_raw.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))        # .../cesfam_app/rem
PROJECT_ROOT = os.path.dirname(BASE_DIR)                     # .../cesfam_app

# Agregamos el PROJECT_ROOT al sys.path para que se pueda importar 'cesfam_app'
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Ahora sí, configuramos Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cesfam_app.settings")

import django
django.setup()

# ================================
# Imports del proyecto
# ================================

from rem.services import procesar_y_guardar


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python rem/etl_guardar_raw.py <archivo.xlsx>")
        sys.exit(1)

    ruta = sys.argv[1]
    nombre_archivo = os.path.basename(ruta)

    print(">> \n")
    print(f"📂 Procesando y guardando RAW del archivo: {nombre_archivo}")

    # OJO: procesar_y_guardar asume que el archivo está en MEDIA_ROOT/rem_uploads
    # y recibe solo el nombre, no la ruta completa
    registros, resumen = procesar_y_guardar(nombre_archivo)

    print("\n✔ Insertado en BD correctamente")
    print(f"Total filas procesadas: {len(registros)}")

    print("\nDetalle:")
    for (rem, sec), cantidad in sorted(resumen.items()):
        print(f"  {rem} - {sec}: {cantidad} filas")
