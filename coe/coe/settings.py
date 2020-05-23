"""
Django settings for coe project.

Generated by 'django-admin startproject' using Django 2.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'n!+$&mpxi^8b1tgi)bffl0*gl$0%(esc&icba-0_p#ptayuz=0'

# SECURITY WARNING: don't run with debug turned on in production!
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'coe.jujuy.gob.ar',]

# Application definition

INSTALLED_APPS = [
    #Autocomplete
    'dal',
    'dal_select2',
    #Django bases
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    #Extras:
    'taggit',
    'tinymce',
    'auditlog',
    'multiselectfield',
    'nested_inline',
    'background_task',
    "fcm_django",
    #Apps Propias
    'core.apps.CoreConfig',
    'consultas.apps.ConsultasConfig',
    'georef.apps.GeorefConfig',
    'noticias.apps.NoticiasConfig',
    'operadores.apps.OperadoresConfig',
    'inscripciones.apps.InscripcionesConfig',
    'tareas.apps.TareasConfig',
    'inventario.apps.InventarioConfig',
    'informacion.apps.InformacionConfig',
    'seguimiento.apps.SeguimientoConfig',
    'app.apps.AppConfigure',
    'geotracking.apps.GeotrackingConfig',
    'permisos.apps.PermisosConfig',
    'denuncias.apps.DenunciasConfig',
    'actas.apps.ActasConfig',
    'documentos.apps.DocumentosConfig',
    'graficos.apps.GraficosConfig',
    'wservices.apps.WservicesConfig',
    'background.apps.BackgroundConfig',
    'provision.apps.ProvisionConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    #Auditoria:
    'auditlog.middleware.AuditlogMiddleware',
]

ROOT_URLCONF = 'coe.urls'

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

WSGI_APPLICATION = 'coe.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# SECURITY WARNING: don't run with debug turned on in production!
import sys
DEBUG = (len(sys.argv) > 1 and sys.argv[1] == 'runserver')# or sys.argv[1] == 'shell' ))
LOADDATA = (len(sys.argv) > 1 and sys.argv[1] == 'loaddata')

#Definicion de permisos para subida de archivos:
FILE_UPLOAD_PERMISSIONS = 0o644

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/
LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/
#Configuraciones Propias
MEDIA_URL = '/archivos/'
MEDIA_ROOT = os.path.join(BASE_DIR, "archivos")
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static_source"),
]

#Sistema de accesos:
LOGIN_URL = 'login'
LOGOUT_URL = 'logout'
LOGIN_REDIRECT_URL = '/'

#Actualizar Statics, no solo nuevas
AWS_PRELOAD_METADATA = True

#Loggin
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'api_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'archivos/logs/apis.txt',
        },
        'signals_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'archivos/logs/signals.txt',
        },
        'tasks_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'archivos/logs/tasks.txt',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'archivos/logs/errors.txt',
        },
    },
    'loggers': {
        'apis': {
            'handlers': ['api_file', ],
            'level': 'INFO',
            'propagate': True,
        },
        'signals': {
            'handlers': ['signals_file', ],
            'level': 'INFO',
            'propagate': True,
        },
        'tasks': {
            'handlers': ['tasks_file', ],
            'level': 'INFO',
            'propagate': True,
        },

        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

#Logout
MIDDLEWARE.append('django.contrib.sessions.middleware.SessionMiddleware')
MIDDLEWARE.append('django_session_timeout.middleware.SessionTimeoutMiddleware')
SESSION_EXPIRE_SECONDS = 60 * 60 # expira en 30minutos
SESSION_EXPIRE_AFTER_LAST_ACTIVITY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

#APIS
GEOPOSITION_GOOGLE_MAPS_API_KEY = ''

#Se evita que se envien mails
SEND_MAIL = True
if DEBUG:
    SEND_MAIL = False
    #DEBUG:
    INTERNAL_IPS = ['127.0.0.1',]#Comentar esta linea para no usar!
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')
    #Definimos todos los paneles del debug que queremos disponibles:
    DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
    ]

#Configuramos Tinymce
TINYMCE_DEFAULT_CONFIG = {
    'plugins': "table,xhtmlxtras,paste,searchreplace",
    'theme': "advanced",
    "theme_advanced_buttons3_add" : "cite,abbr",
    'cleanup_on_startup': True,
    'custom_undo_redo_levels': 10,
    'width': '90%',
    'height': '500px',
}

#Email config
SERVER_EMAIL = 'user@domain.com'
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
EMAIL_HOST = 'hostname.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'user@domain.com'
EMAIL_HOST_PASSWORD = ''
DEFAULT_FROM_EMAIL = 'user@domain.com'

#Obtenemos todas nuestras credenciales secretas
try:
    from .credenciales import *
except ImportError:#Si no logramos importar:
    pass