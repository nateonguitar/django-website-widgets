import importlib
import io
import os
import sys
import tempfile
import uuid
from types import ModuleType
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase, override_settings
from django.urls import include, path

from website_widgets import PageRoutes
from website_widgets.config import WebsiteWidgetsConfig
from website_widgets.management.starter_site import StarterSite


class StarterSiteTestCase(SimpleTestCase):
    """
    `ww_create_app` writes the starter site into a temp project, which is then installed and
    served, so these tests prove the site it writes works, not only that its files exist. Each
    test gets its own app label, since the app's modules are imported for real.
    """

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.project_root = temp_dir.name
        self.app_label = f'starter_{uuid.uuid4().hex[:8]}'
        self.app_folder = os.path.join(self.project_root, self.app_label)
        self.enterContext(patch(
            'website_widgets.config._config_cache',
            WebsiteWidgetsConfig(website_app_name=self.app_label)))

        call_command(
            'ww_create_app',
            '--noinput',
            '--project-root', self.project_root,
            stdout=io.StringIO())

        sys.path.insert(0, self.project_root)
        self.addCleanup(sys.path.remove, self.project_root)
        self.addCleanup(self.forget_app_modules)
        importlib.invalidate_caches()
        self.enterContext(patch.object(PageRoutes, '_routes', {}))
        self.enterContext(override_settings(
            INSTALLED_APPS=[*settings.INSTALLED_APPS, self.app_label],
            STATIC_URL='/static/'))
        # Built once the app is installed, since the include imports its urls.py.
        urlconf = ModuleType('starter_site_test_urlconf')
        urlconf.urlpatterns = [path('', include(f'{self.app_label}.urls'))]
        self.enterContext(override_settings(ROOT_URLCONF=urlconf))

    def forget_app_modules(self):
        for module_name in list(sys.modules):
            if module_name.startswith(self.app_label):
                del sys.modules[module_name]

    def read(self, *path_parts: str) -> str:
        with open(os.path.join(self.app_folder, *path_parts), encoding='utf-8') as file:
            return file.read()

    def write(self, content: str, *path_parts: str):
        with open(os.path.join(self.app_folder, *path_parts), 'w', encoding='utf-8') as file:
            file.write(content)

    def run_upgrade(self) -> str:
        output = io.StringIO()
        call_command('ww_upgrade', '--noinput', '--project-root', self.project_root, stdout=output)
        return output.getvalue()

    def test_starter_site__serves_home_page_with_its_urls_and_data_attribute__when_created(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('<title>Home | My Site</title>', html)
        self.assertIn('data-default-name="world"', html)
        self.assertIn("AppUrls.endpoint_greeting = '/api/greeting/{name}';", html)
        self.assertIn("AppUrls.static_bundled_styles = '/static/bundled\\u002Dstyles.css';", html)
        self.assertIn("AppState.siteName = 'My Site';", html)
        self.assertIn("await App.initController(new HomePageController(), '#home-page');", html)
        self.assertIn('examples/01_movie_manager', html)
        self.assertIn('examples/02_animal_shelter', html)

    def test_starter_site__answers_403_with_forbidden_variant__when_page_always_raises(self):
        response = self.client.get('/forbidden-example')

        self.assertEqual(response.status_code, 403)
        html = response.content.decode()
        self.assertIn('<title>Forbidden | My Site</title>', html)
        self.assertIn('ForbiddenExamplePage always raises ForbiddenException', html)
        self.assertNotIn('Nobody sees this template', html)

    def test_starter_site__answers_json__when_greeting_endpoint_is_called(self):
        response = self.client.get('/api/greeting/Ada')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'message': 'Hello, Ada!'})

    def test_starter_site__passes_routing_checks__when_its_urls_are_included(self):
        self.assertEqual(PageRoutes.check_pages_are_routed(), [])
        self.assertEqual(PageRoutes.check_for_ties(), [])

    def test_starter_site__takes_generated_page_and_widget__when_commands_run(self):
        for command, name in (('ww_create_page', 'about_page'), ('ww_create_widget', 'info_card')):
            call_command(command, name, '--tscontroller', 'true', '--stylesheet', 'true', stdout=io.StringIO())

        main_ts = self.read('ts', 'main.ts')
        self.assertIn("export { AboutPageController } from '../pages/about_page/about_page';", main_ts)
        self.assertIn("export { HomePageController } from '../pages/home_page/home_page';", main_ts)
        self.assertIn("import '../widgets/info_card/info_card.scss';", main_ts)
        about_page_module = importlib.import_module(f'{self.app_label}.pages.about_page.about_page')
        app_page_module = importlib.import_module(f'{self.app_label}.pages.app_page')
        self.assertTrue(issubclass(about_page_module.AboutPage, app_page_module.AppPage))

    def test_starter_site__upgrade_overwrites_framework_and_leaves_starter_files__when_both_were_edited(self):
        self.write('// edited\n', 'ts', 'website_widgets', 'controller.ts')
        self.write('# mine\n', 'pages', 'home_page', 'home_page.py')

        output = self.run_upgrade()

        self.assertNotEqual(self.read('ts', 'website_widgets', 'controller.ts'), '// edited\n')
        self.assertEqual(self.read('pages', 'home_page', 'home_page.py'), '# mine\n')
        self.assertIn('changed    controller.ts', output)

    def test_starter_site__upgrade_says_nothing_about_build_files__when_they_are_unchanged(self):
        output = self.run_upgrade()

        for filename in (*StarterSite.BUILD_CONFIGS, StarterSite.PACKAGE_JSON):
            with self.subTest(filename=filename):
                self.assertNotIn(filename, output)
