import io
import os
import tempfile
from unittest.mock import patch

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase, override_settings

from website_widgets.config import WebsiteWidgetsConfig


class WwCreateAppTestCase(SimpleTestCase):
    """The project root is a temp folder; the test settings have no WEBSITE_WIDGETS."""

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.project_root = temp_dir.name
        self.config = WebsiteWidgetsConfig()
        self.enterContext(patch(
            'website_widgets.management.commands.ww_create_app.get_config',
            side_effect=lambda: self.config))

    def run_create_app(self, *args, answers: list[str] | None = None) -> str:
        output = io.StringIO()
        input_answers = answers or []
        with patch('builtins.input', side_effect=input_answers) as mock_input:
            call_command('ww_create_app', '--project-root', self.project_root, *args, stdout=output, no_color=True)
        self.questions = [
            input_call.args[0]
            for input_call in mock_input.call_args_list
        ]
        return output.getvalue()

    def app_path(self, *path_parts: str) -> str:
        return os.path.join(self.project_root, self.config.website_app_name, *path_parts)

    def read(self, *path_parts: str) -> str:
        file_path = self.app_path(*path_parts)
        with open(file_path, encoding='utf-8') as file:
            return file.read()

    def test_create_app__writes_app_and_docs_folder__when_answer_is_yes(self):
        self.run_create_app(answers=['y', 'n'])

        apps_py = self.read('apps.py')
        self.assertIn("name = 'website'", apps_py)
        self.assertIn('class WebsiteConfig(AppConfig):', apps_py)
        for path in ('__init__.py', 'pages/__init__.py', 'widgets/__init__.py', 'website_widgets_docs/AGENTS.md'):
            with self.subTest(path=path):
                file_path = self.app_path(path)
                file_exists = os.path.isfile(file_path)
                self.assertTrue(file_exists)

    def test_create_app__lists_every_file_then_asks__when_interactive(self):
        output = self.run_create_app(answers=['n'])

        self.assertIn('apps.py', output)
        self.assertIn('package.json', output)
        self.assertIn('  website_widgets_docs/routing.md', output)
        self.assertEqual(self.questions, ['Create these files? [y/N] '])

    def test_create_app__writes_nothing__when_answer_is_the_default(self):
        output = self.run_create_app(answers=[''])

        app_folder = self.app_path()
        app_folder_exists = os.path.exists(app_folder)
        self.assertFalse(app_folder_exists)
        self.assertIn('Nothing was created.', output)

    def test_create_app__creates_without_asking__when_noinput(self):
        self.run_create_app('--noinput')

        apps_py_path = self.app_path('apps.py')
        apps_py_exists = os.path.isfile(apps_py_path)
        self.assertEqual(self.questions, [])
        self.assertTrue(apps_py_exists)

    def test_create_app__says_name_is_the_default__when_settings_have_no_website_widgets(self):
        output = self.run_create_app('--noinput')

        self.assertIn("settings has no WEBSITE_WIDGETS, so the website app takes the default name, 'website'", output)
        self.assertIn("WEBSITE_WIDGETS = WebsiteWidgetsConfig(website_app_name='your_app_name')", output)

    def test_create_app__names_configured_app__when_settings_have_website_widgets(self):
        self.config = WebsiteWidgetsConfig(website_app_name='storefront')

        with override_settings(WEBSITE_WIDGETS=self.config):
            output = self.run_create_app('--noinput')

        apps_py = self.read('apps.py')
        self.assertNotIn('default name', output)
        self.assertIn("Creating the website app 'storefront', from WEBSITE_WIDGETS.website_app_name", output)
        self.assertIn('class StorefrontConfig(AppConfig):', apps_py)

    def test_create_app__prints_next_steps__when_created(self):
        output = self.run_create_app('--noinput')

        self.assertIn("add 'website' to INSTALLED_APPS", output)
        self.assertIn("path('', include('website.urls'))", output)
        self.assertIn('start_npm_watch()', output)
        self.assertIn('npm install', output)
        self.assertIn('Other helpful management commands:', output)
        commands = (
            'ww_create_page',
            'ww_create_widget',
            'ww_create_dialog',
            'ww_show_routes',
            'ww_doctor',
            'ww_test',
            'ww_upgrade',
        )
        for command in commands:
            self.assertIn(f'  {command}', output)

    def test_create_app__writes_starter_site_with_app_label_filled_in__when_configured(self):
        self.config = WebsiteWidgetsConfig(website_app_name='storefront')

        with override_settings(WEBSITE_WIDGETS=self.config):
            self.run_create_app('--noinput')

        app_page_py = self.read('pages', 'app_page.py')
        app_urls_py = self.read('widgets', 'app_urls', 'app_urls.py')
        package_json = self.read('package.json')
        self.assertIn('from storefront.exceptions import', app_page_py)
        self.assertIn("reverse_template('storefront:HomePage')", app_urls_py)
        self.assertIn('"name": "storefront"', package_json)
        filled_paths = (
            'webpack.config.js',
            'tsconfig.json',
            'ts/main.ts',
            'ts/app-state.ts',
            'ts/app-urls.ts',
            'pages/home_page/home_page.ts',
            'endpoints/greeting_endpoint.py',
            'exceptions.py',
        )
        for path in filled_paths:
            with self.subTest(path=path):
                content = self.read(path)
                self.assertNotIn('__app_label__', content)

    def test_create_app__writes_no_template_files__when_created(self):
        self.run_create_app('--noinput')

        app_folder = self.app_path()
        for folder, subfolders, filenames in os.walk(app_folder):
            for filename in filenames:
                with self.subTest(filename=filename):
                    is_template = filename.endswith('.tmpl')
                    self.assertFalse(is_template)

    def test_create_app__fails__when_app_folder_exists(self):
        app_folder = self.app_path()
        os.makedirs(app_folder)

        with self.assertRaisesMessage(CommandError, 'already exists'):
            self.run_create_app('--noinput')

    def test_create_app__fails_pointing_at_upgrade__when_app_is_installed(self):
        self.config = WebsiteWidgetsConfig(website_app_name='website_widgets')

        with self.assertRaisesMessage(CommandError, 'ww_upgrade'):
            self.run_create_app('--noinput')

        app_folder = self.app_path()
        app_folder_exists = os.path.exists(app_folder)
        self.assertFalse(app_folder_exists)
