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
        with patch('builtins.input', side_effect=answers or []) as mock_input:
            call_command('ww_create_app', '--project-root', self.project_root, *args, stdout=output)
        self.questions = [call.args[0] for call in mock_input.call_args_list]
        return output.getvalue()

    def app_path(self, *path_parts: str) -> str:
        return os.path.join(self.project_root, self.config.website_app_name, *path_parts)

    def read(self, *path_parts: str) -> str:
        with open(self.app_path(*path_parts), encoding='utf-8') as file:
            return file.read()

    def test_create_app__writes_app_and_framework_folder__when_answer_is_yes(self):
        self.run_create_app(answers=['y', 'n'])

        self.assertIn("name = 'website'", self.read('apps.py'))
        self.assertIn('class WebsiteConfig(AppConfig):', self.read('apps.py'))
        for path in ('__init__.py', 'pages/__init__.py', 'widgets/__init__.py', 'ts/website_widgets/controller.ts'):
            with self.subTest(path=path):
                self.assertTrue(os.path.isfile(self.app_path(path)))

    def test_create_app__lists_every_file_then_asks__when_interactive(self):
        output = self.run_create_app(answers=['n'])

        self.assertIn('apps.py', output)
        self.assertIn('ts/website_widgets/controller.ts', output)
        self.assertIn('ts/website_widgets/docs/routing.md', output)
        self.assertEqual(self.questions, ['Create these files? [y/N] '])

    def test_create_app__writes_nothing__when_answer_is_the_default(self):
        output = self.run_create_app(answers=[''])

        self.assertFalse(os.path.exists(self.app_path()))
        self.assertIn('Nothing was created.', output)

    def test_create_app__creates_without_asking__when_noinput(self):
        self.run_create_app('--noinput')

        self.assertEqual(self.questions, [])
        self.assertTrue(os.path.isfile(self.app_path('apps.py')))

    def test_create_app__says_name_is_the_default__when_settings_have_no_website_widgets(self):
        output = self.run_create_app('--noinput')

        self.assertIn("settings has no WEBSITE_WIDGETS, so the website app takes the default name, 'website'", output)
        self.assertIn("WEBSITE_WIDGETS = WebsiteWidgetsConfig(website_app_name='your_app_name')", output)

    def test_create_app__names_configured_app__when_settings_have_website_widgets(self):
        self.config = WebsiteWidgetsConfig(website_app_name='storefront')

        with override_settings(WEBSITE_WIDGETS=self.config):
            output = self.run_create_app('--noinput')

        self.assertNotIn('default name', output)
        self.assertIn("Creating the website app 'storefront', from WEBSITE_WIDGETS.website_app_name", output)
        self.assertIn('class StorefrontConfig(AppConfig):', self.read('apps.py'))

    def test_create_app__prints_next_steps__when_created(self):
        output = self.run_create_app('--noinput')

        self.assertIn("Add 'website' to INSTALLED_APPS", output)
        self.assertIn("path('', PageRoutes.urls())", output)

    def test_create_app__fails__when_app_folder_exists(self):
        os.makedirs(self.app_path())

        with self.assertRaisesMessage(CommandError, 'already exists'):
            self.run_create_app('--noinput')

    def test_create_app__fails_pointing_at_upgrade__when_app_is_installed(self):
        self.config = WebsiteWidgetsConfig(website_app_name='website_widgets')

        with self.assertRaisesMessage(CommandError, 'ww_upgrade'):
            self.run_create_app('--noinput')

        self.assertFalse(os.path.exists(self.app_path()))
