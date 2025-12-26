from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent
# Apuntamos al JSON correcto
RUTA_JSON = BASE_DIR / "rem_structures.json"


def es_columna_descriptiva(nombre_campo: str) -> bool:
    """
    Decide si una columna es 'descriptiva' (texto / nivel)
    usando solo el nombre del campo.
    """
    n = nombre_campo.lower()

    if n in {
        "condicion",
        "profesional",
        "tipo_control",
        "tipo_de_control",
        "actividad",
        "diagnostico",
        "grupo_de_pesquisa",
        "descripcion",
        "detalle",
        "motivo",
        "categoria",
    }:
        return True

    if n.startswith(("texto_", "desc_", "nombre_", "etiqueta_")):
        return True

    return False


try:
    with open(RUTA_JSON, "r", encoding="utf-8") as f:
        raw = json.load(f)
except FileNotFoundError:
    REM_STRUCTURES = {}
else:
    REM_STRUCTURES = {}

    # raw = {
    #   "A01": {
    #       "nombre": "...",
    #       "secciones": { "A": {...}, ... }
    #   },
    #   "A11A": { "L": {...} }   # formato antiguo
    # }
    for hoja, info_hoja in raw.items():
        if not isinstance(info_hoja, dict):
            continue

        # Si viene con "secciones", las usamos; si no, usamos el formato antiguo
        if "secciones" in info_hoja and isinstance(info_hoja["secciones"], dict):
            secciones_dict = info_hoja["secciones"]
        else:
            secciones_dict = {
                k: v for k, v in info_hoja.items()
                if isinstance(v, dict)
            }

        for seccion, info_seccion in secciones_dict.items():
            if not isinstance(info_seccion, dict):
                continue

            columnas_def = info_seccion.get("columnas")
            if not columnas_def:
                continue

            # En tu JSON "columnas" ya es la lista de campos finales en orden
            lista_campos = list(columnas_def)

            # Cuántas columnas iniciales son descriptivas (texto)
            num_desc_cols = 0
            for nombre in lista_campos:
                if es_columna_descriptiva(nombre):
                    num_desc_cols += 1
                else:
                    break

            # 👇 tomamos tabla_principal si existe
            tabla_principal = info_seccion.get("tabla_principal")

            entrada = {
                "columnas": lista_campos,
                "num_desc_cols": num_desc_cols,
            }
            if tabla_principal:
                entrada["tabla_principal"] = tabla_principal

            REM_STRUCTURES.setdefault(hoja, {})[seccion] = entrada
