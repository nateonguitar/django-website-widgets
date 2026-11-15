import importlib
import os
from unittest.mock import patch

from django.core.management import CommandError
from django.test import override_settings

from website_widgets.tests.commands.component_test_case import MAIN_TS, ComponentTestCase


class WwCreateWidgetTestCase(ComponentTestCase):
    def create_widget(self, *args: str) -> str:
        return self.run_command('ww_create_widget', *args)

    def list_folder(self, *path_parts: str) -> list[str]:
        folder = os.path.join(*path_parts)
        filenames = os.listdir(folder)
        return sorted(filenames)

    def test_create_widget__writes_widget_files__when_both_flags_true(self):
        self.create_widget('like_button', '--tscontroller', '--stylesheet')

        folder = os.path.join(self.app_folder, 'widgets', 'like_button')
        filenames = self.list_folder(folder)
        init_py = self.read(folder, '__init__.py')
        widget_py = self.read(folder, 'like_button.py')
        html = self.read(folder, 'like_button.html')
        controller_ts = self.read(folder, 'like_button.ts')
        expected_filenames = [
            '__init__.py',
            'like_button.html',
            'like_button.py',
            'like_button.scss',
            'like_button.ts',
        ]
        self.assertEqual(filenames, expected_filenames)
        self.assertIn('from .like_button import LikeButton', init_py)
        self.assertIn('class LikeButton(AsyncWidget):', widget_py)
        self.assertIn('<div id="like-button"', html)
        self.assertIn('data-label="{{ data.label }}"', html)
        self.assertIn("await App.initController(new LikeButtonController(), '#like-button');", html)
        self.assertIn('export class LikeButtonController extends Controller', controller_ts)
        self.assertIn("querySelector('.like-button__label')", controller_ts)

    def test_create_widget__writes_async_widget__when_no_flag_given(self):
        self.create_widget('like_button', '--no-tscontroller', '--no-stylesheet')

        widget_py = self.read(self.app_folder, 'widgets', 'like_button', 'like_button.py')
        self.assertIn('from website_widgets import AsyncWidget', widget_py)
        self.assertIn('class LikeButton(AsyncWidget):', widget_py)
        self.assertIn('    async def set_context(self):', widget_py)

    def test_create_widget__writes_sync_widget__when_sync_flag_given(self):
        self.create_widget('like_button', '--no-tscontroller', '--no-stylesheet', '--sync')

        widget_py = self.read(self.app_folder, 'widgets', 'like_button', 'like_button.py')
        self.assertIn('class LikeButton(SyncWidget):', widget_py)
        self.assertIn('    def set_context(self):', widget_py)
        self.assertNotIn('async', widget_py)

    def test_create_widget__writes_async_widget__when_async_flag_given(self):
        self.create_widget('like_button', '--no-tscontroller', '--no-stylesheet', '--async')

        widget_py = self.read(self.app_folder, 'widgets', 'like_button', 'like_button.py')
        self.assertIn('class LikeButton(AsyncWidget):', widget_py)

    def test_create_widget__fails__when_both_async_and_sync_given(self):
        with self.assertRaises(CommandError):
            self.create_widget('like_button', '--no-tscontroller', '--no-stylesheet', '--async', '--sync')

    def test_create_widget__writes_package_init_for_each_added_folder__when_name_is_nested(self):
        output = self.create_widget('emails/parts/email_document', '--no-tscontroller', '--no-stylesheet')

        for folder in (('emails',), ('emails', 'parts')):
            with self.subTest(folder=folder):
                init_py = self.read(self.app_folder, 'widgets', *folder, '__init__.py')
                self.assertEqual(init_py, '')
        self.assertIn('website/widgets/emails/__init__.py, so its folder imports as a package.', output)
        self.assertIn('website/widgets/emails/parts/__init__.py, so its folder imports as a package.', output)

    def test_create_widget__leaves_existing_folder_as_is__when_name_is_nested_in_it(self):
        emails_folder = os.path.join(self.app_folder, 'widgets', 'emails')
        os.makedirs(emails_folder)
        self.write('# Kept.\n', emails_folder, '__init__.py')

        output = self.create_widget('emails/email_document', '--no-tscontroller', '--no-stylesheet')

        init_py = self.read(emails_folder, '__init__.py')
        self.assertEqual(init_py, '# Kept.\n')
        self.assertNotIn('Also wrote', output)

    def test_create_widget__kebab_cases_root_from_last_part__when_name_is_nested(self):
        self.create_widget('dialogs/login_dialog', '--no-tscontroller', '--no-stylesheet')

        html = self.read(self.app_folder, 'widgets', 'dialogs', 'login_dialog', 'login_dialog.html')
        self.assertIn('<div class="login-dialog"', html)
        self.assertIn('<p>{{ data.label }}</p>', html)

    def test_create_widget__registers_stylesheet_and_controller_sorted__when_both_generated(self):
        self.create_widget('like_button', '--tscontroller', '--stylesheet')

        main_ts = self.read(self.app_folder, 'ts', 'main.ts')
        expected_styles = (
            "// {{ WIDGET STYLES START }}\n"
            "import '../widgets/like_button/like_button.scss';\n"
            "import '../widgets/zebra/zebra.scss';\n"
        )
        expected_controllers = (
            "// {{ WIDGET CONTROLLERS START }}\n"
            "export { LikeButtonController } from '../widgets/like_button/like_button';\n"
        )
        self.assertIn(expected_styles, main_ts)
        self.assertIn(expected_controllers, main_ts)

    def test_create_widget__imports_controller_from_the_npm_package__when_name_is_nested(self):
        self.create_widget('dialogs/login_dialog', '--tscontroller', '--no-stylesheet')

        controller_ts = self.read(self.app_folder, 'widgets', 'dialogs', 'login_dialog', 'login_dialog.ts')
        main_ts = self.read(self.app_folder, 'ts', 'main.ts')
        self.assertIn('import { Controller } from "django-website-widgets";', controller_ts)
        self.assertIn("export { LoginDialogController } from '../widgets/dialogs/login_dialog/login_dialog';", main_ts)

    def test_create_widget__writes_no_controller_or_stylesheet__when_both_declined(self):
        self.create_widget('plain_card', '--no-tscontroller', '--no-stylesheet')

        folder = os.path.join(self.app_folder, 'widgets', 'plain_card')
        filenames = self.list_folder(folder)
        html = self.read(folder, 'plain_card.html')
        main_ts = self.read(self.app_folder, 'ts', 'main.ts')
        self.assertEqual(filenames, ['__init__.py', 'plain_card.html', 'plain_card.py'])
        self.assertNotIn('<script', html)
        self.assertEqual(main_ts, MAIN_TS)

    def test_create_widget__writes_root_with_class_and_no_id__when_no_controller(self):
        cases = (
            ('--no-repeating', 'plain_card_single'),
            ('--repeating', 'plain_card_repeating'),
        )
        for repeating_flag, name in cases:
            with self.subTest(repeating=repeating_flag):
                output = self.create_widget(name, '--no-tscontroller', '--no-stylesheet', repeating_flag)

                folder = os.path.join(self.app_folder, 'widgets', name)
                css_name = name.replace('_', '-')
                html = self.read(folder, f'{name}.html')
                widget_py = self.read(folder, f'{name}.py')
                self.assertIn(f'<div class="{css_name}">', html)
                self.assertNotIn('id=', html)
                self.assertIn('def __init__(self):', widget_py)
                self.assertIn(f'root .{css_name}\n', output)

    def test_create_widget__asks__when_flags_not_given(self):
        with patch('builtins.input', side_effect=['n', '']):
            self.create_widget('asked_card')

        filenames = self.list_folder(self.app_folder, 'widgets', 'asked_card')
        self.assertEqual(filenames, ['__init__.py', 'asked_card.html', 'asked_card.py', 'asked_card.scss'])

    def test_create_widget__uses_project_template__when_templates_dir_has_one(self):
        project_template = '<script type="module" nonce="{{ page.nonce }}">__ClassName__</script>\n'
        self.write(project_template, self.templates_dir, 'widget__controller__single.html.tmpl')

        self.create_widget('like_button', '--tscontroller', '--no-stylesheet')

        folder = os.path.join(self.app_folder, 'widgets', 'like_button')
        html = self.read(folder, 'like_button.html')
        widget_py = self.read(folder, 'like_button.py')
        controller_ts = self.read(folder, 'like_button.ts')
        self.assertEqual(html, '<script type="module" nonce="{{ page.nonce }}">LikeButton</script>\n')
        self.assertIn('class LikeButton(AsyncWidget):', widget_py)
        self.assertIn('export class LikeButtonController', controller_ts)

    def test_create_widget__fails__when_folder_exists(self):
        existing_folder = os.path.join(self.app_folder, 'widgets', 'like_button')
        os.makedirs(existing_folder)

        with self.assertRaisesMessage(CommandError, 'already exists'):
            self.create_widget('like_button', '--no-tscontroller', '--no-stylesheet')

    def test_create_widget__fails_writing_nothing__when_a_part_of_the_name_cannot_be_a_module(self):
        names = ('Like-Button', 'LikeButton', 'like button', 'class', '2fast', '../escape', 'dialogs//login')
        for name in names:
            with self.subTest(name=name):
                with self.assertRaisesMessage(CommandError, "can't be a component name"):
                    self.create_widget(name, '--tscontroller', '--stylesheet')

        widgets_folder = os.path.join(self.app_folder, 'widgets')
        widgets_folder_exists = os.path.exists(widgets_folder)
        app_filenames = self.list_folder(self.app_folder)
        main_ts = self.read(self.app_folder, 'ts', 'main.ts')
        expected_app_filenames = [
            'package.json',
            'ts',
            'tsconfig.json',
            'webpack.config.js',
            'website_widgets_docs',
        ]
        self.assertFalse(widgets_folder_exists)
        self.assertEqual(app_filenames, expected_app_filenames)
        self.assertEqual(main_ts, MAIN_TS)

    def test_create_widget__takes_the_default__when_there_is_no_input_to_read(self):
        with patch('builtins.input', side_effect=EOFError):
            self.create_widget('asked_card')

        filenames = self.list_folder(self.app_folder, 'widgets', 'asked_card')
        expected_filenames = [
            '__init__.py',
            'asked_card.html',
            'asked_card.py',
            'asked_card.scss',
            'asked_card.ts',
        ]
        self.assertEqual(filenames, expected_filenames)

    def test_create_widget__lists_each_file_with_what_it_holds__when_created(self):
        output = self.create_widget('dialogs/login_dialog', '--tscontroller', '--stylesheet', '--sync')

        widget_folder = os.path.join(self.app_folder, 'widgets', 'dialogs', 'login_dialog')
        expected_file_list = (
            f'Created the widget LoginDialog in {widget_folder}/:\n'
            '  __init__.py\n'
            '  login_dialog.py     class LoginDialog(SyncWidget)\n'
            '  login_dialog.html   root #login-dialog\n'
            '  login_dialog.ts     LoginDialogController, exported from ts/main.ts\n'
            '  login_dialog.scss   imported in ts/main.ts\n'
        )
        self.assertIn(expected_file_list, output)

    def test_create_widget__writes_keyed_class_and_root__when_repeating(self):
        cases = (
            ('async_card', '--async', 'async def'),
            ('sync_card', '--sync', 'def'),
        )
        for name, set_context_flag, set_context_definition in cases:
            with self.subTest(set_context=set_context_flag):
                output = self.create_widget(
                    name,
                    '--tscontroller',
                    '--no-stylesheet',
                    '--repeating',
                    set_context_flag)

                folder = os.path.join(self.app_folder, 'widgets', name)
                css_name = name.replace('_', '-')
                widget_py = self.read(folder, f'{name}.py')
                html = self.read(folder, f'{name}.html')
                expected_root = f'<div class="{css_name}"\n     data-key="{{{{ data.key }}}}"'
                expected_selector = f"""'.{css_name}[data-key="{{{{ data.key }}}}"]');"""
                self.assertIn('def __init__(self, *, key):', widget_py)
                self.assertIn(f'    {set_context_definition} set_context(self):', widget_py)
                self.assertIn(expected_root, html)
                self.assertIn(expected_selector, html)
                self.assertNotIn('{% comment %}', html)
                self.assertIn(', taking key=\n', output)
                self.assertIn(f'root .{css_name}[data-key=<key>]', output)

    def test_create_widget__renders_one_key_and_selector_per_instance__when_repeating_widget_is_shown_twice(self):
        self.create_widget('movie_card', '--tscontroller', '--no-stylesheet', '--repeating', '--sync')
        movie_card_module = importlib.import_module('website.widgets.movie_card')
        first_movie_card = movie_card_module.MovieCard(key=1)
        second_movie_card = movie_card_module.MovieCard(key=2)

        with override_settings(STATIC_URL='/static/'):
            first_html = first_movie_card.render__test()
            second_html = second_movie_card.render__test()

        self.assertIn('data-key="1"', first_html)
        self.assertIn("""initController(new MovieCardController(), '.movie-card[data-key="1"]');""", first_html)
        self.assertIn('data-key="2"', second_html)
        self.assertIn("""initController(new MovieCardController(), '.movie-card[data-key="2"]');""", second_html)

    def test_create_widget__asks_whether_repeating__only_when_controller_generated(self):
        with patch('builtins.input', side_effect=['y']) as mock_input:
            self.create_widget('movie_card', '--tscontroller', '--no-stylesheet')

        movie_card_py = self.read(self.app_folder, 'widgets', 'movie_card', 'movie_card.py')
        mock_input.assert_called_once_with('Shown more than once on a page? [y/N] ')
        self.assertIn('key', movie_card_py)

        with patch('builtins.input') as mock_input:
            self.create_widget('plain_card', '--no-tscontroller', '--no-stylesheet')

        plain_card_py = self.read(self.app_folder, 'widgets', 'plain_card', 'plain_card.py')
        mock_input.assert_not_called()
        self.assertNotIn('key', plain_card_py)

    def test_create_widget__writes_single_use_widget__when_repeating_question_is_left_blank(self):
        with patch('builtins.input', side_effect=['']):
            self.create_widget('like_button', '--tscontroller', '--no-stylesheet')

        folder = os.path.join(self.app_folder, 'widgets', 'like_button')
        widget_py = self.read(folder, 'like_button.py')
        html = self.read(folder, 'like_button.html')
        self.assertIn('def __init__(self):', widget_py)
        self.assertIn("'#like-button');", html)

    def test_create_widget__lists_files_without_main_ts_notes__when_main_ts_is_missing(self):
        main_ts_path = os.path.join(self.app_folder, 'ts', 'main.ts')
        os.remove(main_ts_path)

        output = self.create_widget('like_button', '--tscontroller', '--stylesheet')

        file_list = output.split('Created the widget')[1]
        self.assertIn('  like_button.ts     LikeButtonController\n', output)
        self.assertIn('  like_button.scss\n', output)
        self.assertNotIn('ts/main.ts\n', file_list)
