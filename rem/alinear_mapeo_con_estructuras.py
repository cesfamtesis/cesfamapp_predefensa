import os
import json
import csv

MAX_LEN_IDENT = 63  # límite de PostgreSQL


def normalizar_nombre_columna(col_sql: str, usados: set) -> str:
    """
    Misma lógica que usamos para generar 01_crear_tablas_cesfam_raw.sql
    - minúsculas
    - recorte a 63 caracteres
    - si se repite, agrega sufijos _1, _2, ...
    """
    base = (col_sql or "").lower()

    # recortar al límite duro de PostgreSQL
    if len(base) > MAX_LEN_IDENT:
        base = base[:MAX_LEN_IDENT]

    nombre = base
    i = 1
    while nombre in usados:
        sufijo = f"_{i}"
        max_base_len = MAX_LEN_IDENT - len(sufijo)
        nombre = base[:max_base_len] + sufijo
        i += 1

    usados.add(nombre)
    return nombre


def col_letter_to_index(letter: str) -> int:
    """
    Convierte letra de Excel a índice base 0:
    A -> 0, B -> 1, ..., Z -> 25, AA -> 26, AB -> 27, etc.
    """
    letter = letter.strip().upper()
    if not letter:
        raise ValueError("Columna vacía")

    n = 0
    for ch in letter:
        if not ("A" <= ch <= "Z"):
            raise ValueError(f"Letra de columna inválida: {letter}")
        n = n * 26 + (ord(ch) - ord("A") + 1)
    return n - 1


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    ruta_json = os.path.join(base_dir, "rem_structures.json")
    ruta_csv = os.path.join(base_dir, "mapeo_rem.csv")
    ruta_salida = os.path.join(base_dir, "mapeo_rem_alineado.csv")

    if not os.path.exists(ruta_json):
        print(f"ERROR: No se encontró {ruta_json}")
        return
    if not os.path.exists(ruta_csv):
        print(f"ERROR: No se encontró {ruta_csv}")
        return

    # 1) Cargar rem_structures.json
    with open(ruta_json, "r", encoding="utf-8") as f:
        maestro = json.load(f)

    # 2) Pre-calcular, para cada (REM, Sección), la lista de nombres seguros
    estructuras_safe = {}
    for rem_key, secciones in maestro.items():  # rem_key ej: "a01"
        for sec, info in secciones.items():     # sec ej: "A", "B.1"
            usados = {"id_raw", "fila_excel"}
            cols = info.get("columnas_sql") or info.get("columnas") or []
            safe_cols = []
            for col in cols:
                safe_cols.append(normalizar_nombre_columna(col, usados))
            estructuras_safe[(rem_key, sec)] = safe_cols

    # 3) Recorrer mapeo_rem.csv y ajustar campo_destino
    total = 0
    alineados = 0
    sin_estructura = 0
    fuera_rango = 0

    with open(ruta_csv, "r", encoding="utf-8") as fin, \
         open(ruta_salida, "w", encoding="utf-8", newline="") as fout:

        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            total += 1
            hoja = (row.get("hoja") or "").strip().upper()    # ej: A01
            seccion = (row.get("seccion") or "").strip()      # ej: A, B.1
            col_letter = (row.get("columna_excel") or "").strip().upper()

            try:
                idx = col_letter_to_index(col_letter)
            except Exception:
                fuera_rango += 1
                writer.writerow(row)
                continue

            rem_key = hoja.lower()   # "A01" -> "a01"
            clave = (rem_key, seccion)

            if clave not in estructuras_safe:
                sin_estructura += 1
                writer.writerow(row)
                continue

            safe_cols = estructuras_safe[clave]
            if idx < 0 or idx >= len(safe_cols):
                fuera_rango += 1
                writer.writerow(row)
                continue

            nombre_seguro = safe_cols[idx]
            row["campo_destino"] = nombre_seguro
            alineados += 1
            writer.writerow(row)

    print("===========================================")
    print(" Alineación de mapeo_rem.csv completada")
    print(" Archivo de salida:", ruta_salida)
    print("===========================================")
    print(f" Filas totales         : {total}")
    print(f" Filas alineadas       : {alineados}")
    print(f" Sin estructura REM    : {sin_estructura}")
    print(f" Columna fuera de rango: {fuera_rango}")
    print(" (revísalas manualmente si es necesario)")
    print("===========================================")


if __name__ == "__main__":
    main()
