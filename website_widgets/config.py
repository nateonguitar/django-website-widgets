class WebsiteWidgetsConfig:
    def __init__(
        self,
        show_debug_tree: bool = False
    ):
        self.show_debug_tree = show_debug_tree


_config_cache: WebsiteWidgetsConfig | None = None


def get_config() -> WebsiteWidgetsConfig:
    """
    Get the website widgets configuration from Django settings.

    Caches the configuration on first access. If settings.WEBSITE_WIDGETS is not defined,
    uses a default configuration.

    Returns:
        WebsiteWidgetsConfig: The configuration object
    """
    global _config_cache

    if _config_cache is None:
        from django.conf import settings

        if hasattr(settings, 'WEBSITE_WIDGETS'):
            _config_cache = settings.WEBSITE_WIDGETS
        else:
            _config_cache = WebsiteWidgetsConfig()

    return _config_cache
