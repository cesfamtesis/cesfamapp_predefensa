"""
Django settings for cesfam_app project.

Proyecto: Sistema REM CESFAM Ultraestación
Framework: Django 5.2.7
"""

from pathlib import Path
import os
import dj_database_url

# ============================================================
# RUTAS BASE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# CONFIGURACIÓN BÁSICA / SEGURIDAD
# ============================================================

# SECRET KEY (Render friendly)
SECRET_KEY = (
    os.environ.get("SECRET_KEY")
    or os.environ.get("DJANGO_SECRET_KEY")
    or "django-insecure-dev-key"
)

# DEBUG (Render friendly)
DEBUG = (
    os.environ.get("DEBUG")
    or os.environ.get("DJANGO_DEBUG")
    or "False"
) == "True"

# ALLOWED HOSTS (Render friendly)
_raw_hosts = (
    os.environ.get("ALLOWED_HOSTS")
    or os.environ.get("DJANGO_ALLOWED_HOSTS")
    or "localhost,127.0.0.1,.onrender.com"
)

ALLOWED_HOSTS = [h.strip() for h in _raw_hosts.split(",") if h.strip()]


# ============================================================
# APLICACIONES INSTALADAS
# ============================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps del proyecto
    'rem',
    'accounts',
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    # WhiteNoise para Render
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # Middleware propio: fuerza validación 2FA
    'accounts.middleware.TwoFAMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ============================================================
# URLS Y TEMPLATES
# ============================================================

ROOT_URLCONF = 'cesfam_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'cesfam_app.wsgi.application'


# ============================================================
# BASE DE DATOS (Render / Local)
# ============================================================

DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True,
    )
}


# ============================================================
# VALIDACIÓN DE CONTRASEÑAS
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ============================================================
# INTERNACIONALIZACIÓN
# ============================================================

LANGUAGE_CODE = 'es-cl'
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True


# ============================================================
# ARCHIVOS ESTÁTICOS
# ============================================================

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# ============================================================
# ARCHIVOS MEDIA
# ============================================================

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ============================================================
# AUTENTICACIÓN Y REDIRECCIONES
# ============================================================

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "accounts:login"


# ============================================================
# SEGURIDAD DE SESIÓN
# ============================================================

SESSION_COOKIE_AGE = 900  # 15 minutos
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True


# ============================================================
# CSRF (RENDER)
# ============================================================

CSRF_TRUSTED_ORIGINS = [
    "https://cesfamapp-predefensa.onrender.com",
]


# ============================================================
# CONFIGURACIÓN DE CORREO (2FA) - SENDGRID SMTP ✅
# ============================================================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

# SendGrid SMTP requiere:
# USER = "apikey"
# PASSWORD = SENDGRID_API_KEY
EMAIL_HOST_USER = "apikey"
EMAIL_HOST_PASSWORD = os.environ.get("SENDGRID_API_KEY")

EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = "cesfamtesis@gmail.com"


# ============================================================
# CONFIGURACIÓN FINAL
# ============================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
