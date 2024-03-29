import os


BASE_DIR = os.path.dirname(os.path.dirname(__file__))


SECRET_KEY = 'fake-key'


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.staticfiles',

    'adminsortable2',
    'ckeditor',
    'django_simple_bulk_emailer',
    'django_simple_file_handler',
    'tests',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'tests', 'templates'),
        ],
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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


TIME_ZONE = 'UTC'

USE_TZ = True


ROOT_URLCONF = 'tests.urls'


MEDIA_ROOT = os.path.join(BASE_DIR, 'tests/media/')


STATIC_URL = '/static/'

MEDIA_URL = '/media/'


DEFAULT_FROM_EMAIL = 'Test Account <example@example.com>'

SERVER_EMAIL = DEFAULT_FROM_EMAIL


SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']
