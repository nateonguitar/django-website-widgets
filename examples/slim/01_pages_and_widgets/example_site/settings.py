"""
Settings for running the example locally. Not for deploying: the secret key is public and
`DEBUG` is on.
"""

import os
from pathlib import Path

from website_widgets.config import WebsiteWidgetsConfig


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-website-widgets-example-pages-and-widgets'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'website_widgets',
    'website',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'example_site.urls'

# Widget templates are read from beside their classes; this backend compiles them.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
}

# `SHOW_DEBUG_TREE=1 python manage.py runserver` draws each page's widget tree under it.
WEBSITE_WIDGETS = WebsiteWidgetsConfig(
    show_debug_tree=os.environ.get('SHOW_DEBUG_TREE') == '1',
)

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
USE_TZ = True
