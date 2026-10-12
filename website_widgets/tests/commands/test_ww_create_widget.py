import os
from unittest.mock import patch

from django.core.management import CommandError

from website_widgets.tests.commands.component_test_case import MAIN_TS, ComponentTestCase


class WwCreateWidgetTestCase(ComponentTestCase):
    def create_widget(self, *args: str) -> str:
        return self.run_command('ww_create_widget', *args)

    def test_create_widget__writes_widget_files__when_both_flags_true(self):
        self.create_widget('like_button', '--tscontroller=true', '--stylesheet=true')

        folder = os.path.join(self.app_folder, 'widgets', 'like_button')
        self.assertEqual(
            sorted(os.listdir(folder)),
            ['__init__.py', 'like_button.html', 'like_button.py', 'like_button.scss', 'like_button.ts'])
        self.assertIn('from .like_button import LikeButton', self.read(folder, '__init__.py'))
        self.assertIn('class LikeButton(Widget):', self.read(folder, 'like_button.py'))
        self.assertIn('LikeButtonController.initializeController();', self.read(folder, 'like_button.html'))
        self.assertIn('export class LikeButtonController extends Controller', self.read(folder, 'like_button.ts'))

    def test_create_widget__registers_stylesheet_and_controller_sorted__when_both_generated(self):
        self.create_widget('like_button', '--tscontroller=true', '--stylesheet=true')

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

    def test_create_widget__imports_framework_relative_to_depth__when_name_is_nested(self):
        self.create_widget('dialogs/login_dialog', '--tscontroller=true', '--stylesheet=false')

        controller_ts = self.read(self.app_folder, 'widgets', 'dialogs', 'login_dialog', 'login_dialog.ts')
        self.assertIn('from "../../../ts/website_widgets/app"', controller_ts)
        self.assertIn(
            "export { LoginDialogController } from '../widgets/dialogs/login_dialog/login_dialog';",
            self.read(self.app_folder, 'ts', 'main.ts'))

    def test_create_widget__writes_no_controller_or_stylesheet__when_both_declined(self):
        self.create_widget('plain_card', '--tscontroller=false', '--stylesheet=false')

        folder = os.path.join(self.app_folder, 'widgets', 'plain_card')
        self.assertEqual(sorted(os.listdir(folder)), ['__init__.py', 'plain_card.html', 'plain_card.py'])
        self.assertNotIn('<script', self.read(folder, 'plain_card.html'))
        self.assertEqual(self.read(self.app_folder, 'ts', 'main.ts'), MAIN_TS)

    def test_create_widget__asks__when_flags_not_given(self):
        with patch('builtins.input', side_effect=['n', '']):
            self.create_widget('asked_card')

        folder = os.path.join(self.app_folder, 'widgets', 'asked_card')
        self.assertEqual(sorted(os.listdir(folder)), ['__init__.py', 'asked_card.html', 'asked_card.py', 'asked_card.scss'])

    def test_create_widget__uses_project_template__when_templates_dir_has_one(self):
        self.write('<script type="module" nonce="{{ page.nonce }}">__ClassName__</script>\n',
                   self.templates_dir, 'component__controller.html.tmpl')

        self.create_widget('like_button', '--tscontroller=true', '--stylesheet=false')

        folder = os.path.join(self.app_folder, 'widgets', 'like_button')
        self.assertEqual(
            self.read(folder, 'like_button.html'),
            '<script type="module" nonce="{{ page.nonce }}">LikeButton</script>\n')
        self.assertIn('class LikeButton(Widget):', self.read(folder, 'like_button.py'))
        self.assertIn('export class LikeButtonController', self.read(folder, 'like_button.ts'))

    def test_create_widget__fails_pointing_at_upgrade__when_framework_files_are_missing(self):
        os.remove(os.path.join(self.app_folder, 'ts', 'website_widgets', 'controller.ts'))

        with self.assertRaisesMessage(CommandError, 'ww_upgrade'):
            self.create_widget('like_button', '--tscontroller=true', '--stylesheet=false')

    def test_create_widget__fails__when_folder_exists(self):
        os.makedirs(os.path.join(self.app_folder, 'widgets', 'like_button'))

        with self.assertRaisesMessage(CommandError, 'already exists'):
            self.create_widget('like_button', '--tscontroller=false', '--stylesheet=false')
