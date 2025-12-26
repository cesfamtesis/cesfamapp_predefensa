#!/usr/bin/env bash
set -o errexit  # Detiene el build si ocurre cualquier error

# =====================================
# 1) Instalar dependencias del proyecto
# =====================================
pip install -r requirements.txt

# =====================================
# 2) Recolectar archivos estáticos
#    (WhiteNoise / Render)
# =====================================
python manage.py collectstatic --noinput

# =====================================
# 3) Aplicar migraciones a la base de datos
#    (PostgreSQL vía DATABASE_URL)
# =====================================
python manage.py migrate --noinput