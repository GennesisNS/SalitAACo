"""
Django settings for the salitaaco project.

Every secret and environment-specific value is read from the environment
(see .env.example). The defaults suit local development.
"""

from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "t", "yes", "y", "on")


def env_list(name: str, default=None):
    val = os.getenv(name)
    if not val:
        return default or []
    return [item.strip() for item in val.split(",") if item.strip()]


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-change-me-in-the-env-file")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_bool("DJANGO_DEBUG", True)

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ["localhost", "127.0.0.1"])

# The Django admin is not the back office; it is only mounted when this is on.
SHOW_ADMIN_ROUTES = env_bool("SHOW_ADMIN_ROUTES", False)


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'salitaaco',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

X_FRAME_OPTIONS = 'SAMEORIGIN'
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", [])

ROOT_URLCONF = 'salitaaco.urls'
WSGI_APPLICATION = 'salitaaco.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'salitaaco.context_processors.dashboard_navigations.navigation_items',
                'salitaaco.context_processors.current_account.current_account',
            ],
        },
    },
]


# Database
# The engine is chosen explicitly with DB_ENGINE ("sqlite" or "mysql").

DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").strip().lower()

if DB_ENGINE == "mysql":
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv("DB_NAME", "salitaaco"),
            'USER': os.getenv("DB_USER", "root"),
            'PASSWORD': os.getenv("DB_PASSWORD", ""),
            'HOST': os.getenv("DB_HOST", "localhost"),
            'PORT': os.getenv("DB_PORT", "3306"),
            'OPTIONS': {'charset': 'utf8mb4'},
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / os.getenv("DB_NAME", "db.sqlite3"),
        }
    }

# The PHP application's database, read once by `manage.py import_php_data`.
# It is not a Django database: the command reads it with the MySQL driver
# directly, because Django refuses servers older than it supports (XAMPP ships
# MariaDB 10.4; Django 5.2 needs 10.5).
LEGACY_DATABASE = {
    'NAME': os.getenv("LEGACY_DB_NAME", ""),
    'USER': os.getenv("LEGACY_DB_USER", "root"),
    'PASSWORD': os.getenv("LEGACY_DB_PASSWORD", ""),
    'HOST': os.getenv("LEGACY_DB_HOST", "localhost"),
    'PORT': int(os.getenv("LEGACY_DB_PORT", "3306")),
}


# Text to speech and voice cloning with ElevenLabs.
# ELEVENLABS_VOICE_ID is the shared Filipino voice that `manage.py generate_tile_audio`
# voices the tile words in. Family voices are cloned from the guardians' recordings.
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")


# Authentication

AUTHENTICATION_BACKENDS = ['salitaaco.authentication.custom_authentication.UsernameBackend']
LOGIN_URL = '/login/'

# New passwords use Django's default hasher. The bcrypt hasher is listed so that
# accounts imported from the PHP application (password_hash() output, stored as
# "bcrypt$<hash>") keep their current password; Django re-hashes it on next login.
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
]

# The only password rule is the four-character minimum carried over from the
# PHP application, which is enforced by the forms.
AUTH_PASSWORD_VALIDATORS = []


# Internationalization

LANGUAGE_CODE = 'en-us'

TIME_ZONE = os.getenv("TIME_ZONE", "Asia/Manila")

USE_I18N = True

USE_TZ = True


# Static files and uploads

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"

# Uploads are private to the account that owns them. They are served by
# login-protected views, never straight from MEDIA_URL.
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DATA_UPLOAD_MAX_MEMORY_SIZE = 25 * 1024 * 1024  # 25 MB

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Logging

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = BASE_DIR / "logs" / "salitaaco.log"
LOG_FILE.parent.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '{asctime} {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': LOG_FILE,
            'formatter': 'standard',
            'encoding': 'utf-8',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': LOG_LEVEL,
    },
}
