"""
The settings the library's tests run under. Every test is a `SimpleTestCase`, so no database is
configured; tests that need URLs set `ROOT_URLCONF` themselves.
"""

SECRET_KEY = 'website-widgets-tests'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'website_widgets',
]

ROOT_URLCONF = 'website_widgets.tests.urls'

# Widget templates are compiled with `Template()`, which needs a DjangoTemplates backend.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
    },
]

USE_TZ = True
