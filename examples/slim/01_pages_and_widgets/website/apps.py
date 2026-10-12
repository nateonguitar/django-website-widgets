from django.apps import AppConfig


class WebsiteConfig(AppConfig):
    """
    The site's pages and widgets. Named `website`, `WebsiteWidgetsConfig.website_app_name`'s
    default, so `@register_url` finds its pages with no setting.
    """

    name = 'website'
