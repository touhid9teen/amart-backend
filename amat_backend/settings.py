import os
from pathlib import Path
from decouple import config


# Add these at the top of your settings.py
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qsl

load_dotenv()

# -------------------------------
# ✅ BASE DIRECTORY
# -------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------------
# ✅ SECURITY SETTINGS
# -------------------------------
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(',')

# -------------------------------
# ✅ APPLICATIONS
# -------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'corsheaders',

    # your apps
    'users',
    'store',
    'order',
]

# -------------------------------
# ✅ MIDDLEWARE
# -------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# -------------------------------
# ✅ URLS / WSGI
# -------------------------------
ROOT_URLCONF = 'amat_backend.urls'
WSGI_APPLICATION = 'amat_backend.wsgi.application'

# -------------------------------
# ✅ TEMPLATES
# -------------------------------
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
            ],
        },
    },
]

# -------------------------------
# ✅ DATABASE
# -------------------------------
# Replace the DATABASES section of your settings.py with this
tmpPostgres = urlparse(os.getenv("DATABASE_URL"))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': tmpPostgres.path.replace('/', ''),
        'USER': tmpPostgres.username,
        'PASSWORD': tmpPostgres.password,
        'HOST': tmpPostgres.hostname,
        'PORT': 5432,
        'OPTIONS': dict(parse_qsl(tmpPostgres.query)),
    }
}

# -------------------------------
# ✅ CUSTOM USER MODEL
# -------------------------------
AUTH_USER_MODEL = 'users.User'

# -------------------------------
# ✅ AUTHENTICATION BACKENDS
# -------------------------------
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # Default Django auth backend (supports email-based user model)
]

# -------------------------------
# ✅ PASSWORD VALIDATORS
# -------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -------------------------------
# ✅ INTERNATIONALIZATION
# -------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Dhaka'
USE_I18N = True
USE_TZ = True

# -------------------------------
# ✅ STATIC & MEDIA
# -------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# -------------------------------
# ✅ DEFAULT PRIMARY KEY FIELD
# -------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# -------------------------------
# ✅ REST FRAMEWORK
# -------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'users.authenticatin.CustomAuthentication',
    ),
}

# -------------------------------
# ✅ JWT SETTINGS
# -------------------------------
JWT_SECRET_KEY = config("JWT_SECRET_KEY", default=SECRET_KEY)
JWT_ACCESS_TOKEN_LIFETIME_HOURS = config("JWT_ACCESS_TOKEN_LIFETIME_HOURS", default=1, cast=int)
JWT_REFRESH_TOKEN_LIFETIME_DAYS = config("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=7, cast=int)

# -------------------------------
# ✅ CORS SETTINGS
# -------------------------------
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='http://localhost:3000').split(',')

CORS_ALLOW_HEADERS = ["content-type", "authorization"]

# -------------------------------
# ✅ ARENA SMS SETTINGS
# -------------------------------
ARENA_SMS_API_URL = config("ARENA_SMS_API_URL", default=None)
ARENA_SMS_API_ACODE = config("ARENA_SMS_API_ACODE", default=None)
ARENA_SMS_API_KEY = config("ARENA_SMS_API_KEY", default=None)
ARENA_SMS_MASKING = config("ARENA_SMS_MASKING", default=None)

# -------------------------------
# ✅ EMAIL SETTINGS
# -------------------------------
if DEBUG:
    # For development: use console backend to see emails in terminal
    # EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    # For production/testing: use SMTP
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False

EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
RECIPIENT_EMAILS = [email.strip() for email in config('EMAIL_RECIPIENTS', default='').split(',') if email.strip()]

# Email timeout
EMAIL_TIMEOUT = 10

# Validate email configuration
import logging
logger = logging.getLogger(__name__)

if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
    logger.warning("⚠️  EMAIL CONFIGURATION WARNING:")
    if not EMAIL_HOST_USER:
        logger.warning("   - EMAIL_HOST_USER is not set")
    if not EMAIL_HOST_PASSWORD:
        logger.warning("   - EMAIL_HOST_PASSWORD is not set")
    logger.warning("   Email sending will fail! Please configure email credentials.")
    logger.warning("   See PRODUCTION_EMAIL_FIX.md for setup instructions.")
else:
    logger.info(f"✅ Email configured: {EMAIL_HOST_USER}")
