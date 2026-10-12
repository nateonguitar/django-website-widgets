from django.apps import AppConfig


class WebsiteConfig(AppConfig):
    """The site's views and widgets. It has no pages, so route discovery has nothing to find."""

    name = 'website'
