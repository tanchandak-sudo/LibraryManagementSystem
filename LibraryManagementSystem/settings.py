# import os
# from pathlib import Path
# from dotenv import load_dotenv

# # Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent

# # Load environment variables from .env file
# load_dotenv(BASE_DIR / '.env')


# # Quick-start development settings - unsuitable for production
# SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-8f#k29!v-0a9z(x1m^@4lq+c8b*u7_y%3w!d+e5g&r6t1n2p3s')

# # Turn off DEBUG in production using environment variables
# DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')


# # Application definition

# INSTALLED_APPS = [
#     'django.contrib.admin',
#     'django.contrib.auth',
#     'django.contrib.contenttypes',
#     'django.contrib.sessions',
#     'django.contrib.messages',
#     'django.contrib.staticfiles',
#     'drf_spectacular',
    
#     # Local Apps
#     'books',
#     'users',
#     'rest',
#     'payments',
#     'reports',
    
#     # Third-Party Apps
#     'rest_framework',
# ]

# MIDDLEWARE = [
#     'django.middleware.security.SecurityMiddleware',
#     # Serves static files efficiently in production via Gunicorn
#     'whitenoise.middleware.WhiteNoiseMiddleware',
#     'django.contrib.sessions.middleware.SessionMiddleware',
#     'django.middleware.common.CommonMiddleware',
#     'django.middleware.csrf.CsrfViewMiddleware',
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'django.contrib.messages.middleware.MessageMiddleware',
#     'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
#     # Custom Rate Limiting Middleware
#     'LibraryManagementSystem.middleware.RateLimit429Middleware',
# ]

# ROOT_URLCONF = 'LibraryManagementSystem.urls'

# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [BASE_DIR / 'templates'],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.debug',
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = 'LibraryManagementSystem.wsgi.application'


# # Database Configuration
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.environ.get('DB_NAME', 'library_system'),
#         'USER': os.environ.get('DB_USER', 'postgres'),
#         'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
#         'HOST': os.environ.get('DB_HOST', 'localhost'),
#         'PORT': os.environ.get('DB_PORT', '5432'),
#         'CONN_MAX_AGE': 600,  # Keeps database connections persistent
#     }
# }


# # Password validation
# AUTH_PASSWORD_VALIDATORS = [
#     {
#         'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
#     },
# ]


# # Caching configuration
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#         'LOCATION': 'unique-snowflake',
#     }
# }


# # Internationalization
# LANGUAGE_CODE = 'en-us'
# TIME_ZONE = 'UTC'
# USE_I18N = True
# USE_TZ = True


# # Static and Media Files Configuration
# STATIC_URL = '/static/'

# # Source directory for custom project static assets
# STATICFILES_DIRS = [BASE_DIR / 'static']

# # Target directory where collectstatic copies files (Fixes ImproperlyConfigured error)
# STATIC_ROOT = BASE_DIR / 'staticfiles'

# # WhiteNoise production storage backend with compression
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# MEDIA_URL = '/media/'
# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# PROTECTED_MEDIA_ROOT = os.path.join(BASE_DIR, 'protected_media')

# DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# # Razorpay Credentials (Pulled from Environment Variables)
# RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_TTazZIHlXnIglk')
# RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 'Z0g6k1OdsZ7tfnxFOsU348zn')


# # Authentication Redirect URLs
# LOGIN_URL = 'login'
# LOGIN_REDIRECT_URL = 'books:book_list'
# LOGOUT_REDIRECT_URL = 'login'


# # Email Configuration
# EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
# EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
# EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
# EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'

# EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

# SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
# SENDGRID_SANDBOX_MODE_IN_DEBUG = False

# DEFAULT_FROM_EMAIL = os.environ.get(
#     'DEFAULT_FROM_EMAIL', 
#     'Library Management System <noreply@yourdomain.com>'
# )
# SERVER_EMAIL = DEFAULT_FROM_EMAIL


# # Django REST Framework Settings
# REST_FRAMEWORK = {
#     'DEFAULT_THROTTLE_CLASSES': [
#         'rest_framework.throttling.AnonRateThrottle',
#         'rest_framework.throttling.UserRateThrottle',
#         'rest_framework.throttling.ScopedRateThrottle',
#     ],
#     'DEFAULT_THROTTLE_RATES': {
#         'anon': '20/hour',
#         'user': '1000/day',
#         'checkout': '10/minute',
#         'search': '30/minute',
#     },
#     'DEFAULT_AUTHENTICATION_CLASSES': [
#         'rest_framework.authentication.SessionAuthentication',
#         'rest_framework.authentication.BasicAuthentication',
#     ],
#     'DEFAULT_PERMISSION_CLASSES': [
#         'rest_framework.permissions.IsAuthenticatedOrReadOnly',
#     ],
#     'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
#     'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
#     'PAGE_SIZE': 10,
# }

# SPECTACULAR_SETTINGS = {
#     'TITLE': 'Library Management System API',
#     'DESCRIPTION': 'API documentation for Catalog, Cart, and Subscriptions',
#     'VERSION': '1.0.0',
#     'SERVE_INCLUDE_SCHEMA': False,
#     'SCHEMA_PATH_PREFIX': r'/api/',
# }


# # Production Security Headers (Active when DEBUG=False)
# if not DEBUG:
#     SECURE_BROWSER_XSS_FILTER = True
#     SECURE_CONTENT_TYPE_NOSNIFF = True
#     SESSION_COOKIE_SECURE = True
#     CSRF_COOKIE_SECURE = True
#     SECURE_SSL_REDIRECT = True
#     SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
#     SECURE_HSTS_SECONDS = 31536000
#     SECURE_HSTS_INCLUDE_SUBDOMAINS = True
#     SECURE_HSTS_PRELOAD = True

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env', override=True)

SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'drf_spectacular',
    
    # Local Apps
    'books',
    'users',
    'rest',
    'payments',
    'reports',
    
    # Third-Party Apps
    'rest_framework',
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
    'LibraryManagementSystem.middleware.RateLimit429Middleware',
]

ROOT_URLCONF = 'LibraryManagementSystem.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'LibraryManagementSystem.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'library_system'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
    }
}

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
PROTECTED_MEDIA_ROOT = os.path.join(BASE_DIR, 'protected_media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Dynamic Payment Keys fetched from .env
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'books:book_list'
LOGOUT_REDIRECT_URL = 'login'

EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Library System <noreply@yourdomain.com>')

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Library Management System API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True