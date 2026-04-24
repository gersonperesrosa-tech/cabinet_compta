from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

# Charger le fichier .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET KEY
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

# DEBUG
DEBUG = os.environ.get("DEBUG") == "True"

# ALLOWED HOSTS
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps du projet
    'cabinet_compta.apps.CabinetComptaConfig',
    'widget_tweaks',
    'dossiers',
    'paie',
    'cloture',
    'administration',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cabinet_compta.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'dossiers.context_processors.last_fiscal_year',
                'dossiers.context_processors.cloture_context',
                'cabinet_compta.context_processors.user_role',
                'cabinet_compta.context_processors.latest_cloture_year',
            ],
        },
    },
]

WSGI_APPLICATION = 'cabinet_compta.wsgi.application'

# DATABASES — local = SQLite, Render = PostgreSQL
DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr'
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

# STATIC FILES
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"

LOGIN_URL = "/login/"
LOGOUT_REDIRECT_URL = "/login/"

# ============================================
# EMAIL — CONFIGURATION SENDINBLUE (BREVO)
# ============================================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp-relay.brevo.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# ⚠️ À REMPLIR AVEC TES INFOS SENDINBLUE
EMAIL_HOST_USER = os.environ.get("BREVO_SMTP_LOGIN")
EMAIL_HOST_PASSWORD = os.environ.get("BREVO_SMTP_PASSWORD")

DEFAULT_FROM_EMAIL = os.environ.get("EMAIL_SENDER")

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

