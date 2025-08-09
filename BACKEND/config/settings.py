import os
import logging
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
import dj_database_url


# Chemin de base du projet (le dossier BACKEND)
BASE_DIR = Path(__file__).resolve().parent.parent

# Charger les variables d'environnement depuis le fichier .env situé à la racine du BACKEND.
# C'est la première chose à faire pour que les variables soient disponibles partout.
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Initialisation du logger
logger = logging.getLogger(__name__)

# Custom user model
AUTH_USER_MODEL = 'play_reports.User'

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
# Le mode DEBUG est activé localement, mais sera désactivé en production sur Render.
# Render définit automatiquement la variable d'environnement RENDER.
DEBUG = os.getenv('RENDER') != 'True'

ALLOWED_HOSTS = []

# Récupère le nom d'hôte externe fourni par Render.
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Configuration CORS
CORS_ALLOWED_ORIGINS = [
    "https://datastudio.google.com",
]

# Si vous voulez être plus permissif (utile pour le développement)
CORS_ALLOW_ALL_ORIGINS = True # Attention en production

CSRF_TRUSTED_ORIGINS = [
    'https://*.ngrok-free.app', # Permettre les requêtes POST depuis ngrok
    'https://datastudio.google.com',
]

INSTALLED_APPS = [
    # Local apps (must be first to override templates)
    'play_reports',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework_simplejwt.token_blacklist',
    
    # Third-party apps
    'rest_framework',
    'corsheaders',
    'rest_framework.authtoken', # Requis pour la clé API de Looker Studio
    'django_celery_beat',
]

# Middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', # Doit être avant CommonMiddleware
    'play_reports.middleware.CoepMiddleware', # Ajout pour la politique COEP
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Whitenoise doit être placé juste après SecurityMiddleware pour de meilleures performances.
]

# Configuration CORS nettoyée et centralisée
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
# Ajoute l'URL du frontend hébergé si elle est définie
FRONTEND_URL = os.getenv('FRONTEND_URL')
if FRONTEND_URL:
    CORS_ALLOWED_ORIGINS.append(FRONTEND_URL)

# Expressions régulières pour les domaines Google
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.google\.com$",
]

# En-têtes et méthodes autorisés
CORS_ALLOW_HEADERS = "*"
CORS_ALLOW_METHODS = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']

ROOT_URLCONF = 'config.urls' 

# Templates
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

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Configuration de la base de données
# On essaie de construire DATABASE_URL à partir des autres variables d'environnement si elle n'existe pas.
if 'DATABASE_URL' not in os.environ:
    db_user = os.getenv('POSTGRES_USER')
    db_password = os.getenv('POSTGRES_PASSWORD')
    db_host = os.getenv('POSTGRES_HOST')
    db_port = os.getenv('POSTGRES_PORT')
    db_name = os.getenv('POSTGRES_DB')

    if all([db_user, db_password, db_host, db_port, db_name]):
        os.environ['DATABASE_URL'] = f"postgres://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

DATABASES = {
    'default': dj_database_url.config(conn_max_age=600, ssl_require=False, default='sqlite:///db.sqlite3')
}

# JWT settings
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication', # Requis pour la clé API de Looker Studio
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ]
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(
        minutes=int(os.environ.get('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', 60))
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        days=int(os.environ.get('JWT_REFRESH_TOKEN_LIFETIME_DAYS', 1))
    ),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Custom user model
AUTH_USER_MODEL = 'play_reports.User'


# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'play_reports.backends.EmailBackend',
]

# Celery configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Static and media files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Configuration de Whitenoise pour la production
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Frontend
FRONTEND_URL = "http://localhost:3000"

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # Replace with your SMTP server
EMAIL_PORT = 587  # Common port for TLS
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'benhassen.farah@esprit.tn')  # Your email
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'tvbz qmjg rvis wvnw')  # Your email password
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Ou 'file' ou 'cache' selon votre configuration
SESSION_COOKIE_SECURE = True  # En production avec HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_SAVE_EVERY_REQUEST = True

# Session settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_SAVE_EVERY_REQUEST = True

# Authentication URLs
LOGIN_URL = '/play-reports/auth/login/'
LOGIN_REDIRECT_URL = '/play-reports/display-gcs-files/'
LOGOUT_REDIRECT_URL = '/play-reports/'

# Autoriser le frontend React (tournant sur localhost:3000) à se connecter
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Créer le répertoire static s'il n'existe pas
os.makedirs(os.path.join(BASE_DIR, 'static'), exist_ok=True)

# Google Cloud Configuration
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME', 'pubsite_prod_rev_17712529971520156702')
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID', 'pc-api-4722596725443039036-618')

# Assurez-vous que le fichier de credentials est accessible
if GOOGLE_APPLICATION_CREDENTIALS and not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
    logger.warning(f"Fichier de credentials Google Cloud non trouvé à l'emplacement: {GOOGLE_APPLICATION_CREDENTIALS}")