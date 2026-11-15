import importlib
import os
from unittest.mock import patch

from django.core.management import CommandError

from website_widgets.tests.commands.component_test_case import MAIN_TS, ComponentTestCase


class WwCreateDialogTestCase(ComponentTestCase):
    def create_dialog(self, *args: str) -> str:
        return self.run_command('ww_create_dialog', *args)

    def test_create_dialog__writes_dialog_files__when_stylesheet_flag_given(self):
        self.create_dialog('confirm_dialog', '--stylesheet')

        folder = os.path.join(self.app_folder, 'widgets', 'confirm_dialog')
        filenames = sorted(os.listdir(folder))
        init_py = self.read(folder, '__init__.py')
        dialog_py = self.read(folder, 'confirm_dialog.py')
        html = self.read(folder, 'confirm_dialog.html')
        controller_ts = self.read(folder, 'confirm_dialog.ts')
        expected_filenames = [
            '__init__.py',
            'confirm_dialog.html',
            'confirm_dialog.py',
            'confirm_dialog.scss',
            'confirm_dialog.ts',
        ]
        self.assertEqual(filenames, expected_filenames)
        self.assertIn('from .confirm_dialog import ConfirmDialog', init_py)
        self.assertIn('class ConfirmDialog(SyncWidget):', dialog_py)
        self.assertIn('<template id="confirm-dialog-template"', html)
        self.assertIn('data-dialog-class="confirm-dialog"', html)
        self.assertIn('export class ConfirmDialogController extends DialogController<void>', controller_ts)
        self.assertIn('"#confirm-dialog-template"', controller_ts)

    def test_create_dialog__registers_stylesheet_and_controller_sorted__when_stylesheet_generated(self):
        self.create_dialog('confirm_dialog', '--stylesheet')

        main_ts = self.read(self.app_folder, 'ts', 'main.ts')
        expected_styles = (
            "// {{ WIDGET STYLES START }}\n"
            "import '../widgets/confirm_dialog/confirm_dialog.scss';\n"
            "import '../widgets/zebra/zebra.scss';\n"
        )
        expected_controllers = (
            "// {{ WIDGET CONTROLLERS START }}\n"
            "export { ConfirmDialogController } from '../widgets/confirm_dialog/confirm_dialog';\n"
        )
        self.assertIn(expected_styles, main_ts)
        self.assertIn(expected_controllers, main_ts)

    def test_create_dialog__writes_controller_and_no_stylesheet__when_stylesheet_declined(self):
        self.create_dialog('confirm_dialog', '--no-stylesheet')

        folder = os.path.join(self.app_folder, 'widgets', 'confirm_dialog')
        filenames = sorted(os.listdir(folder))
        main_ts = self.read(self.app_folder, 'ts', 'main.ts')
        expected_filenames = [
            '__init__.py',
            'confirm_dialog.html',
            'confirm_dialog.py',
            'confirm_dialog.ts',
        ]
        self.assertEqual(filenames, expected_filenames)
        self.assertNotIn('confirm_dialog.scss', main_ts)
        self.assertIn("export { ConfirmDialogController } from '../widgets/confirm_dialog/confirm_dialog';", main_ts)

    def test_create_dialog__asks_only_for_the_stylesheet__when_flag_not_given(self):
        with patch('builtins.input', side_effect=['n']) as mock_input:
            self.create_dialog('confirm_dialog')

        folder = os.path.join(self.app_folder, 'widgets', 'confirm_dialog')
        filenames = os.listdir(folder)
        mock_input.assert_called_once_with('Generate a stylesheet? [Y/n] ')
        self.assertNotIn('confirm_dialog.scss', filenames)

    def test_create_dialog__renders_a_template_with_its_title__when_rendered(self):
        self.create_dialog('confirm_dialog', '--no-stylesheet')
        confirm_dialog_module = importlib.import_module('website.widgets.confirm_dialog')
        confirm_dialog = confirm_dialog_module.ConfirmDialog()

        html = confirm_dialog.render__test()

        starts_with_template = html.startswith('<template id="confirm-dialog-template"')
        self.assertTrue(starts_with_template)
        self.assertIn('data-dialog-label>ConfirmDialog</h2>', html)
        self.assertIn('data-dialog-close>', html)

    def test_create_dialog__imports_controller_relative_to_main_ts__when_name_is_nested(self):
        output = self.create_dialog('dialogs/login_dialog', '--no-stylesheet')

        folder = os.path.join(self.app_folder, 'widgets', 'dialogs', 'login_dialog')
        html = self.read(folder, 'login_dialog.html')
        dialogs_init_py = self.read(self.app_folder, 'widgets', 'dialogs', '__init__.py')
        main_ts = self.read(self.app_folder, 'ts', 'main.ts')
        self.assertIn('<template id="login-dialog-template"', html)
        self.assertEqual(dialogs_init_py, '')
        self.assertIn('website/widgets/dialogs/__init__.py, so its folder imports as a package.', output)
        self.assertIn("export { LoginDialogController } from '../widgets/dialogs/login_dialog/login_dialog';", main_ts)

    def test_create_dialog__uses_project_template__when_templates_dir_has_one(self):
        project_template = '<template id="__css_name__-template" data-dialog-class="dialog __css_name__"></template>\n'
        self.write(project_template, self.templates_dir, 'dialog.html.tmpl')

        self.create_dialog('confirm_dialog', '--no-stylesheet')

        folder = os.path.join(self.app_folder, 'widgets', 'confirm_dialog')
        html = self.read(folder, 'confirm_dialog.html')
        dialog_py = self.read(folder, 'confirm_dialog.py')
        controller_ts = self.read(folder, 'confirm_dialog.ts')
        expected_html = '<template id="confirm-dialog-template" data-dialog-class="dialog confirm-dialog"></template>\n'
        self.assertEqual(html, expected_html)
        self.assertIn('class ConfirmDialog(SyncWidget):', dialog_py)
        self.assertIn('extends DialogController<void>', controller_ts)

    def test_create_dialog__fails__when_folder_exists(self):
        existing_folder = os.path.join(self.app_folder, 'widgets', 'confirm_dialog')
        os.makedirs(existing_folder)

        with self.assertRaisesMessage(CommandError, 'already exists'):
            self.create_dialog('confirm_dialog', '--stylesheet')

    def test_create_dialog__fails_writing_nothing__when_a_part_of_the_name_cannot_be_a_module(self):
        for name in ('Confirm-Dialog', 'ConfirmDialog', 'class', '../escape'):
            with self.subTest(name=name):
                with self.assertRaisesMessage(CommandError, "can't be a component name"):
                    self.create_dialog(name, '--stylesheet')

        widgets_folder = os.path.join(self.app_folder, 'widgets')
        widgets_folder_exists = os.path.exists(widgets_folder)
        main_ts = self.read(self.app_folder, 'ts', 'main.ts')
        self.assertFalse(widgets_folder_exists)
        self.assertEqual(main_ts, MAIN_TS)

    def test_create_dialog__lists_each_file_and_how_to_open_it__when_created(self):
        output = self.create_dialog('dialogs/login_dialog', '--stylesheet')

        dialog_folder = os.path.join(self.app_folder, 'widgets', 'dialogs', 'login_dialog')
        expected_file_list = (
            f'Created the dialog LoginDialog in {dialog_folder}/:\n'
            '  __init__.py\n'
            '  login_dialog.py     class LoginDialog(SyncWidget)\n'
            '  login_dialog.html   template #login-dialog-template\n'
            '  login_dialog.ts     LoginDialogController, exported from ts/main.ts\n'
            '  login_dialog.scss   imported in ts/main.ts\n'
        )
        expected_next_step = (
            'Place LoginDialog() as a child of the page or widget it opens from, and open it with '
            '`await LoginDialogController.show()`.'
        )
        self.assertIn(expected_file_list, output)
        self.assertIn(expected_next_step, output)

    def test_create_dialog__lists_files_without_main_ts_notes__when_main_ts_is_missing(self):
        main_ts_path = os.path.join(self.app_folder, 'ts', 'main.ts')
        os.remove(main_ts_path)

        output = self.create_dialog('confirm_dialog', '--stylesheet')

        self.assertIn('  confirm_dialog.ts     ConfirmDialogController\n', output)
        self.assertIn('  confirm_dialog.scss\n', output)
