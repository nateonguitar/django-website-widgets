import os


class GenerateComponentConfig:
    """
    Settings read only by `generate_component`, passed to `WebsiteWidgetsConfig` as
    `generate_component`. Both have defaults, so a project keeping init's layout needs none.
    """

    def __init__(
        self,
        app_page_class: str | None = None,
        templates_dir: str | os.PathLike | None = None,
    ):
        # A dotted path to the base class of a generated page. None means
        # `<website_app_name>.pages.app_page.AppPage`, where init creates one.
        self.app_page_class = app_page_class
        # A folder of the project's own generator templates. A file there replaces the
        # package's template of the same name; the others keep the package's.
        self.templates_dir = os.fspath(templates_dir) if templates_dir is not None else None

    def get_app_page_class(self, website_app_name: str) -> str:
        if self.app_page_class is not None:
            return self.app_page_class
        return f'{website_app_name}.pages.app_page.AppPage'


class WebsiteWidgetsConfig:
    def __init__(
        self,
        show_debug_tree: bool = False,
        website_app_name: str = 'website',
        generate_component: GenerateComponentConfig | None = None,
    ):
        self.show_debug_tree = show_debug_tree
        # An app label, resolved through the app registry, so nothing depends on the working
        # directory.
        self.website_app_name = website_app_name
        self.generate_component = generate_component or GenerateComponentConfig()


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
