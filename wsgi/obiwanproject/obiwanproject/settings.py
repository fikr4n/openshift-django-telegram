"""
Django settings for obiwanproject project.

Generated by 'django-admin startproject' using Django 1.9.4.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WSGI_DIR = os.path.dirname(BASE_DIR)
LOG_DIR = os.environ.get('OPENSHIFT_LOG_DIR') or os.path.join(BASE_DIR, 'log')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# echo -n ... > $OPENSHIFT_HOMEDIR/.env/user_vars/DJANGO_SECRET_KEY
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

# echo -n ... > $OPENSHIFT_HOMEDIR/.env/user_vars/DJANGO_DEBUG
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if os.environ.get('DJANGO_DEBUG') == 'true' else False

from socket import gethostname
ALLOWED_HOSTS = [
    gethostname(), # For internal OpenShift load balancer security purposes.
    os.environ.get('OPENSHIFT_APP_DNS'), # Dynamically map to the OpenShift gear name.
]


# Application definition

INSTALLED_APPS = [
    'obiwankenoweb',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'obiwanproject.urls'

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

WSGI_APPLICATION = 'obiwanproject.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

if os.environ.get('OPENSHIFT_APP_NAME'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ['OPENSHIFT_APP_NAME'],
            'USER': os.environ['OPENSHIFT_POSTGRESQL_DB_USERNAME'],
            'PASSWORD': os.environ['OPENSHIFT_POSTGRESQL_DB_PASSWORD'],
            'HOST': os.environ['OPENSHIFT_POSTGRESQL_DB_HOST'],
            'PORT': os.environ['OPENSHIFT_POSTGRESQL_DB_PORT']
        }
    }
else:  # use sqlite for local
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'id'

TIME_ZONE = 'Asia/Jakarta'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(WSGI_DIR, 'static')


# Logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%Y-%m-%d %H:%M:%S",
        },
        'simple': {
            'format': '[%(asctime)s] %(levelname)s %(message)s',
            'datefmt' : "%Y-%m-%d %H:%M:%S",
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'django_w.log'),
            'formatter': 'verbose',
        },
        'file_tgramupd': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'django_tgramupd.log'),
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
        'obiwankenoweb.views.tgramupd': {
            'handlers': ['file_tgramupd'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}


# Security
# https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

if os.environ.get('OPENSHIFT_APP_NAME'):
	# If your entire site is served only over SSL, you may want to consider setting a
	# value and enabling HTTP Strict Transport Security. Be sure to read the
	# documentation first; enabling HSTS carelessly can cause serious, irreversible
	# problems.
	SECURE_HSTS_SECONDS = 30 * 24 * 60 * 60

	# Without this, your site is potentially vulnerable to attack via an insecure
	# connection to a subdomain. Only set this to True if you are certain that all
	# subdomains of your domain should be served exclusively via SSL.
	#SECURE_HSTS_INCLUDE_SUBDOMAINS = True

	# If SECURE_CONTENT_TYPE_NOSNIFF setting is not set to True, your pages will not be
	# served with an 'x-content-type-options: nosniff' header. You should consider
	# enabling this header to prevent the browser from identifying content types
	# incorrectly.
	SECURE_CONTENT_TYPE_NOSNIFF = True

	# If SECURE_BROWSER_XSS_FILTER setting is not set to True, your pages will not be
	# served with an 'x-xss-protection: 1; mode=block' header. You should consider
	# enabling this header to activate the browser's XSS filtering and help prevent XSS
	# attacks
	SECURE_BROWSER_XSS_FILTER = True

	# Unless your site should be available over both SSL and non-SSL connections, you
	# may want to either set this setting True or configure a load balancer or
	# reverse-proxy server to redirect all connections to HTTPS.
	SECURE_SSL_REDIRECT = True

	# Using a secure-only session cookie makes it more difficult for network traffic
	# sniffers to hijack user sessions.
	SESSION_COOKIE_SECURE = True

	# Using a secure-only CSRF cookie makes it more difficult for network traffic
	# sniffers to steal the CSRF token.
	CSRF_COOKIE_SECURE = True

	# Using an HttpOnly CSRF cookie makes it more difficult for cross-site scripting
	# attacks to steal the CSRF token.
	CSRF_COOKIE_HTTPONLY = True

	# The default is 'SAMEORIGIN', but unless there is a good reason for your site to
	# serve other parts of itself in a frame, you should change it to 'DENY'.
	X_FRAME_OPTIONS = 'DENY'

