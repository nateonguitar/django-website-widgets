import os
from collections.abc import Sequence


class GenerateComponentConfig:
    """
    Settings read only by `ww_create_page`, `ww_create_widget` and `ww_create_dialog`, passed to
    `WebsiteWidgetsConfig` as `generate_component`. All have defaults, so a project keeping
    `ww_create_app`'s layout needs none.
    """

    def __init__(
        self,
        app_page_class: str | None = None,
        templates_dir: str | os.PathLike | None = None,
    ):
        # A dotted path to the base class of a generated page. None means
        # `<website_app_name>.pages.app_page.AppPage`, where the website app keeps its page base class.
        self.app_page_class = app_page_class
        # A folder of the project's own generator templates. A file there replaces the
        # package's template of the same name; the others keep the package's.
        self.templates_dir = os.fspath(templates_dir) if templates_dir is not None else None

    def get_app_page_class(self, website_app_name: str) -> str:
        if self.app_page_class is not None:
            return self.app_page_class
        return f'{website_app_name}.pages.app_page.AppPage'


class TestingConfig:
    """
    Settings read only by `WebsiteWidgetsTestRunner`, passed to `WebsiteWidgetsConfig` as
    `testing`. All have defaults, so a project keeping the starter site's `package.json` needs none.
    """

    # The starter site's dev build, which package.json defines as `build`.
    DEFAULT_BUILD_COMMAND = ('npm', 'run', 'build')

    def __init__(
        self,
        build_command: Sequence[str] | None = DEFAULT_BUILD_COMMAND,
        browser_test_tag: str = 'playwright',
    ):
        # What the runner runs in the website app's folder before a run holding browser tests,
        # so they serve the current bundle. A list of arguments, run without a shell. None: no build.
        if isinstance(build_command, str):
            raise TypeError(
                f'build_command is a list of arguments, run without a shell: write '
                f'{build_command.split()!r}, not {build_command!r}.')
        self.build_command = list(build_command) if build_command is not None else None
        # The Django test tag (`@tag(...)`) marking a test that serves the built bundle.
        self.browser_test_tag = browser_test_tag


class WebsiteWidgetsConfig:
    def __init__(
        self,
        show_debug_tree: bool = False,
        website_app_name: str = 'website',
        generate_component: GenerateComponentConfig | None = None,
        testing: TestingConfig | None = None,
    ):
        self.show_debug_tree = show_debug_tree
        # An app label, resolved through the app registry, so nothing depends on the working
        # directory.
        self.website_app_name = website_app_name
        self.generate_component = generate_component or GenerateComponentConfig()
        self.testing = testing or TestingConfig()


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
