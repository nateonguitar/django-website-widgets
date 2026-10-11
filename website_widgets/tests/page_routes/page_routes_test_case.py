import importlib
import os
import sys
import tempfile
import uuid
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from website_widgets import PageRoutes


class PageRoutesTestCase(SimpleTestCase):
    """
    Each test gets an empty registry and a throwaway website app on `sys.path`, so neither the
    project's pages nor another test's leak in.
    """

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.package_name = f'page_routes_fixture_{uuid.uuid4().hex}'
        package_folder = os.path.join(temp_dir.name, self.package_name)
        self.pages_folder = os.path.join(package_folder, 'pages')
        os.makedirs(self.pages_folder)
        sys.path.insert(0, temp_dir.name)
        self.addCleanup(sys.path.remove, temp_dir.name)
        self.addCleanup(self.forget_fixture_modules)

        app_config = SimpleNamespace(
            name=self.package_name,
            path=package_folder)
        mock_apps = self.enterContext(patch('website_widgets.page_routes.apps'))
        mock_apps.get_app_config.return_value = app_config
        self.enterContext(patch.object(PageRoutes, '_routes', {}))

    def forget_fixture_modules(self):
        for module_name in list(sys.modules):
            if module_name.startswith(self.package_name):
                del sys.modules[module_name]

    def write_page_module(self, relative_path: str, content: str):
        module_path = os.path.join(self.pages_folder, relative_path)
        os.makedirs(os.path.dirname(module_path), exist_ok=True)
        with open(module_path, 'w') as module_file:
            module_file.write(content)
        importlib.invalidate_caches()

    def get_routes_in_url_order(self) -> list[str]:
        url_patterns, _app_name, _namespace = PageRoutes.urls()
        return [str(url_pattern.pattern) for url_pattern in url_patterns]

    def use_urlconf(self, urlpatterns: list):
        urlconf = ModuleType('page_routes_test_urlconf')
        urlconf.urlpatterns = urlpatterns
        self.enterContext(override_settings(ROOT_URLCONF=urlconf))
