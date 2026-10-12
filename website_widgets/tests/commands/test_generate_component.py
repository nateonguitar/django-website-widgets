import io
import os
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase

from website_widgets.config import GenerateComponentConfig, WebsiteWidgetsConfig


MAIN_TS = '''\
// {{ WIDGET STYLES START }}
import '../widgets/zebra/zebra.scss';
// {{ WIDGET STYLES END }}

// {{ PAGE STYLES START }}
// {{ PAGE STYLES END }}

// {{ WIDGET CONTROLLERS START }}
// {{ WIDGET CONTROLLERS END }}

// {{ PAGE CONTROLLERS START }}
// {{ PAGE CONTROLLERS END }}
'''


class GenerateComponentTestCase(SimpleTestCase):
    """A temp website app that init has populated, with a main.ts holding the four marker pairs."""

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.project_root = temp_dir.name
        self.app_folder = os.path.join(self.project_root, 'website')
        self.templates_dir = os.path.join(self.project_root, 'generator_templates')
        os.makedirs(os.path.join(self.app_folder, 'ts'))
        os.makedirs(self.templates_dir)
        self.write(MAIN_TS, self.app_folder, 'ts', 'main.ts')

        app_config = SimpleNamespace(path=self.app_folder)
        for module in ('init_website_widgets', 'generate_component'):
            mock_apps = self.enterContext(patch(f'website_widgets.management.commands.{module}.apps'))
            mock_apps.get_app_config.return_value = app_config
        self.config = WebsiteWidgetsConfig(
            generate_component=GenerateComponentConfig(
                app_page_class='website_widgets.web_page.WebPage',
                templates_dir=self.templates_dir))
        self.enterContext(patch(
            'website_widgets.management.commands.generate_component.get_config',
            side_effect=lambda: self.config))

        call_command(
            'init_website_widgets',
            '--noinput',
            '--project-root',
            self.project_root,
            stdout=io.StringIO())

    def generate(self, *args: str) -> str:
        output = io.StringIO()
        call_command('generate_component', *args, stdout=output, stderr=output)
        return output.getvalue()

    def read(self, *path_parts: str) -> str:
        with open(os.path.join(*path_parts), encoding='utf-8') as file:
            return file.read()

    def write(self, content: str, *path_parts: str):
        with open(os.path.join(*path_parts), 'w', encoding='utf-8') as file:
            file.write(content)

    def test_generate_component__writes_widget_files__when_type_is_widget(self):
        self.generate('widget', 'like_button', '--tscontroller=true', '--stylesheet=true')

        folder = os.path.join(self.app_folder, 'widgets', 'like_button')
        self.assertEqual(
            sorted(os.listdir(folder)),
            ['__init__.py', 'like_button.html', 'like_button.py', 'like_button.scss', 'like_button.ts'])
        self.assertIn('from .like_button import LikeButton', self.read(folder, '__init__.py'))
        self.assertIn('class LikeButton(Widget):', self.read(folder, 'like_button.py'))
        self.assertIn('LikeButtonController.initializeController();', self.read(folder, 'like_button.html'))
        self.assertIn('export class LikeButtonController extends Controller', self.read(folder, 'like_button.ts'))

    def test_generate_component__registers_stylesheet_and_controller_sorted__when_both_generated(self):
        self.generate('widget', 'like_button', '--tscontroller=true', '--stylesheet=true')

        main_ts = self.read(self.app_folder, 'ts', 'main.ts')
        self.assertIn(
            "// {{ WIDGET STYLES START }}\n"
            "import '../widgets/like_button/like_button.scss';\n"
            "import '../widgets/zebra/zebra.scss';\n",
            main_ts)
        self.assertIn(
            "// {{ WIDGET CONTROLLERS START }}\n"
            "export { LikeButtonController } from '../widgets/like_button/like_button';\n",
            main_ts)

    def test_generate_component__extends_app_page_class__when_type_is_page(self):
        self.generate('page', 'home_page', '--tscontroller=false', '--stylesheet=false')

        page_py = self.read(self.app_folder, 'pages', 'home_page', 'home_page.py')
        self.assertIn('from website_widgets.web_page import WebPage', page_py)
        self.assertIn('class HomePage(WebPage):', page_py)

    def test_generate_component__imports_framework_relative_to_depth__when_name_is_nested(self):
        self.generate('widget', 'dialogs/login_dialog', '--tscontroller=true', '--stylesheet=false')

        controller_ts = self.read(self.app_folder, 'widgets', 'dialogs', 'login_dialog', 'login_dialog.ts')
        self.assertIn('from "../../../ts/website_widgets/app"', controller_ts)
        self.assertIn(
            "export { LoginDialogController } from '../widgets/dialogs/login_dialog/login_dialog';",
            self.read(self.app_folder, 'ts', 'main.ts'))

    def test_generate_component__writes_no_controller_or_stylesheet__when_both_declined(self):
        self.generate('widget', 'plain_card', '--tscontroller=false', '--stylesheet=false')

        folder = os.path.join(self.app_folder, 'widgets', 'plain_card')
        self.assertEqual(sorted(os.listdir(folder)), ['__init__.py', 'plain_card.html', 'plain_card.py'])
        self.assertNotIn('<script', self.read(folder, 'plain_card.html'))
        self.assertEqual(self.read(self.app_folder, 'ts', 'main.ts'), MAIN_TS)

    def test_generate_component__asks__when_flags_not_given(self):
        with patch('builtins.input', side_effect=['n', '']):
            self.generate('widget', 'asked_card')

        folder = os.path.join(self.app_folder, 'widgets', 'asked_card')
        self.assertEqual(sorted(os.listdir(folder)), ['__init__.py', 'asked_card.html', 'asked_card.py', 'asked_card.scss'])

    def test_generate_component__uses_project_template__when_templates_dir_has_one(self):
        self.write('<script type="module" nonce="{{ page.nonce }}">__ClassName__</script>\n',
                   self.templates_dir, 'component__controller.html.tmpl')

        self.generate('widget', 'like_button', '--tscontroller=true', '--stylesheet=false')

        folder = os.path.join(self.app_folder, 'widgets', 'like_button')
        self.assertEqual(
            self.read(folder, 'like_button.html'),
            '<script type="module" nonce="{{ page.nonce }}">LikeButton</script>\n')
        self.assertIn('class LikeButton(Widget):', self.read(folder, 'like_button.py'))
        self.assertIn('export class LikeButtonController', self.read(folder, 'like_button.ts'))

    def test_generate_component__ships_templates_with_no_opinions__when_defaults_used(self):
        templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'generator_templates')
        for filename in os.listdir(templates_dir):
            content = self.read(templates_dir, filename).lower()
            for opinion in ('nonce', 'logger', 'loglabel', 'gametabs', 'fetch('):
                with self.subTest(template=filename, opinion=opinion):
                    self.assertNotIn(opinion, content)

    def test_generate_component__fails__when_framework_files_are_missing(self):
        os.remove(os.path.join(self.app_folder, 'ts', 'website_widgets', 'controller.ts'))

        with self.assertRaisesMessage(CommandError, 'init_website_widgets'):
            self.generate('widget', 'like_button', '--tscontroller=true', '--stylesheet=false')

    def test_generate_component__fails_naming_the_path__when_app_page_class_does_not_exist(self):
        self.config.generate_component.app_page_class = 'website.pages.app_page.AppPage'

        with self.assertRaisesMessage(CommandError, 'website.pages.app_page.AppPage'):
            self.generate('page', 'home_page', '--tscontroller=false', '--stylesheet=false')

        self.assertFalse(os.path.exists(os.path.join(self.app_folder, 'pages', 'home_page')))

    def test_generate_component__fails__when_app_page_class_is_not_a_page(self):
        self.config.generate_component.app_page_class = 'website_widgets.widget.Widget'

        with self.assertRaises(CommandError):
            self.generate('page', 'home_page', '--tscontroller=false', '--stylesheet=false')

    def test_generate_component__fails__when_folder_exists(self):
        os.makedirs(os.path.join(self.app_folder, 'widgets', 'like_button'))

        with self.assertRaisesMessage(CommandError, 'already exists'):
            self.generate('widget', 'like_button', '--tscontroller=false', '--stylesheet=false')
