import contextlib
import importlib.metadata
import io
import json
import os
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase

from website_widgets.management.commands import ww_upgrade
from website_widgets.management.framework_folder import FrameworkFolder
from website_widgets.management.starter_site import StarterSite


PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The pointer 0.7.0's commands added, before the docs moved out of ts/website_widgets/.
OLD_POINTER_LINE = (
    '- `website/ts/website_widgets/AGENTS.md` — how django-website-widgets works; read before '
    'changing pages, widgets or controllers')

# What 0.7.0 wrote into ts/website_widgets/, the docs among the TypeScript, and its README's file list.
FILES_0_7_0 = (
    'app.ts',
    'completer.ts',
    'controller.ts',
    'AGENTS.md',
    'docs/creating_and_upgrading_an_app.md',
    'docs/creating_pages_and_widgets.md',
    'docs/frontend_controllers.md',
    'docs/npm_watch.md',
    'docs/rendering_pipeline.md',
    'docs/reverse_template.md',
    'docs/routing.md',
)
README_0_7_0 = (
    '# website_widgets frontend framework\n\n'
    'Copied from django-website-widgets 0.7.0 by `python manage.py ww_upgrade` or `ww_create_app`.\n\n'
    '<!-- website_widgets:files -->\n'
    + ''.join(f'- `{path}`\n' for path in FILES_0_7_0)
    + '- `README.md`\n'
    '<!-- /website_widgets:files -->\n')


class WwUpgradeTestCase(SimpleTestCase):
    """The website app and the project root are temp folders; no real project is touched."""

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.project_root = temp_dir.name
        self.app_folder = os.path.join(self.project_root, 'website')
        self.framework_folder = os.path.join(self.app_folder, 'ts', 'website_widgets')
        self.docs_folder = os.path.join(self.app_folder, 'website_widgets_docs')
        os.makedirs(self.app_folder)

        mock_apps = self.enterContext(patch('website_widgets.management.commands.ww_upgrade.apps'))
        mock_apps.get_app_config.return_value = SimpleNamespace(path=self.app_folder)
        self.mock_apps = mock_apps

    def run_upgrade(
        self,
        *args,
        answers: list[str] | type[EOFError] | None = None
    ) -> str:
        """`answers` are typed in turn; `EOFError` stands for a closed stdin, as in a script."""
        output = io.StringIO()
        with patch('builtins.input', side_effect=answers or []) as mock_input:
            call_command('ww_upgrade', '--project-root', self.project_root, *args, stdout=output)
        self.questions = [call.args[0] for call in mock_input.call_args_list]
        return output.getvalue()

    def read(self, *path_parts: str) -> str:
        with open(os.path.join(*path_parts), encoding='utf-8') as file:
            return file.read()

    def write(self, content: str, *path_parts: str):
        path = os.path.join(*path_parts)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as file:
            file.write(content)

    def test_upgrade__writes_typescript_and_docs_into_their_folders__when_folders_are_missing(self):
        self.run_upgrade('--noinput')

        self.assertEqual(
            self.read(self.framework_folder, 'controller.ts'),
            self.read(PACKAGE_DIR, 'frontend', 'controller.ts'))
        self.assertEqual(
            self.read(self.docs_folder, 'AGENTS.md'),
            self.read(PACKAGE_DIR, 'docs', 'AGENTS.md'))
        self.assertEqual(
            self.read(self.docs_folder, 'routing.md'),
            self.read(PACKAGE_DIR, 'docs', 'routing.md'))
        self.assertEqual(sorted(os.listdir(self.framework_folder)), ['README.md', 'app.ts', 'completer.ts', 'controller.ts'])
        self.assertFalse(os.path.exists(os.path.join(self.docs_folder, 'docs')))

    def test_upgrade__stamps_each_readme_with_version_and_its_files__when_run(self):
        self.run_upgrade('--noinput')

        version = importlib.metadata.version('django-website-widgets')
        files_by_folder = {
            self.framework_folder: ('app.ts', 'controller.ts', 'completer.ts', 'README.md'),
            self.docs_folder: ('AGENTS.md', 'routing.md', 'README.md'),
        }
        for folder, paths in files_by_folder.items():
            readme = self.read(folder, 'README.md')
            self.assertIn(version, readme)
            for path in paths:
                with self.subTest(folder=folder, path=path):
                    self.assertIn(f'- `{path}`', readme)

    def test_upgrade__moves_docs_out_of_typescript_folder__when_app_has_the_old_layout(self):
        self.run_upgrade('--noinput')
        readme_path = os.path.join(self.framework_folder, 'README.md')
        readme = self.read(readme_path)
        self.write(readme.replace('- `README.md`', '- `AGENTS.md`\n- `docs/routing.md`\n- `README.md`'), readme_path)
        self.write('# Old\n', self.framework_folder, 'AGENTS.md')
        self.write('# Old\n', self.framework_folder, 'docs', 'routing.md')

        output = self.run_upgrade('--noinput')

        self.assertFalse(os.path.exists(os.path.join(self.framework_folder, 'AGENTS.md')))
        self.assertFalse(os.path.exists(os.path.join(self.framework_folder, 'docs')))
        self.assertIn('removed    docs/routing.md (moved to website/website_widgets_docs/)', output.replace(self.project_root + os.sep, ''))
        self.assertEqual(self.read(self.docs_folder, 'routing.md'), self.read(PACKAGE_DIR, 'docs', 'routing.md'))

    def test_upgrade__brings_the_folder_0_7_0_wrote_up_to_date__when_upgrading_from_0_7_0(self):
        self.write(README_0_7_0, self.framework_folder, 'README.md')
        for path in FILES_0_7_0:
            self.write(f'0.7.0 {path}\n', self.framework_folder, path)
        self.write('// mine\n', self.framework_folder, 'my_helper.ts')

        output = self.run_upgrade('--noinput')

        self.assertEqual(
            sorted(os.listdir(self.framework_folder)),
            ['README.md', 'app.ts', 'completer.ts', 'controller.ts', 'my_helper.ts'])
        self.assertEqual(self.read(self.framework_folder, 'my_helper.ts'), '// mine\n')
        self.assertEqual(self.read(self.docs_folder, 'routing.md'), self.read(PACKAGE_DIR, 'docs', 'routing.md'))
        shown_output = output.replace(self.project_root + os.sep, '')
        self.assertIn('changed    controller.ts', shown_output)
        self.assertIn('removed    AGENTS.md (moved to website/website_widgets_docs/)', shown_output)
        self.assertIn('removed    docs/routing.md (moved to website/website_widgets_docs/)', shown_output)
        with patch('website_widgets.management.framework_folder.apps', self.mock_apps):
            self.assertEqual(FrameworkFolder.check_version_stamp(), [])

    def test_upgrade__restores_a_package_file__when_it_was_deleted(self):
        self.run_upgrade('--noinput')
        os.remove(os.path.join(self.framework_folder, 'completer.ts'))

        output = self.run_upgrade('--noinput')

        self.assertEqual(
            self.read(self.framework_folder, 'completer.ts'),
            self.read(PACKAGE_DIR, 'frontend', 'completer.ts'))
        self.assertIn('added      completer.ts', output)

    def test_upgrade__leaves_package_file_alone__when_it_differs_only_in_line_endings(self):
        self.run_upgrade('--noinput')
        controller_path = os.path.join(self.framework_folder, 'controller.ts')
        crlf_content = self.read(PACKAGE_DIR, 'frontend', 'controller.ts').replace('\n', '\r\n')
        with open(controller_path, 'w', encoding='utf-8', newline='') as file:
            file.write(crlf_content)

        output = self.run_upgrade('--noinput')

        self.assertIn('ts/website_widgets/ is already up to date', output)
        with open(controller_path, encoding='utf-8', newline='') as file:
            self.assertEqual(file.read(), crlf_content)

    def test_upgrade__runs_no_system_checks__when_run_from_manage_py(self):
        # call_command() skips the checks for every command, so this runs it the way manage.py does.
        argv = ['manage.py', 'ww_upgrade', '--noinput', '--project-root', self.project_root]
        with patch('django.core.checks.run_checks') as mock_run_checks, contextlib.redirect_stdout(io.StringIO()):
            ww_upgrade.Command().run_from_argv(argv)

        mock_run_checks.assert_not_called()

    def test_upgrade__keeps_edited_webpack_config_and_asks_nothing_more__when_there_is_no_input_to_read(self):
        self.write('// tuned\n', self.app_folder, 'webpack.config.js')
        self.write('# Project\n', self.project_root, 'CLAUDE.md')

        output = self.run_upgrade(answers=EOFError)

        self.assertEqual(self.read(self.app_folder, 'webpack.config.js'), '// tuned\n')
        self.assertEqual(self.read(self.project_root, 'CLAUDE.md'), '# Project\n')
        self.assertIn('Kept ', output)

    def test_upgrade__prints_the_error_and_leaves_package_json__when_it_is_not_a_json_object(self):
        self.write('[]\n', self.app_folder, 'package.json')

        output = self.run_upgrade('--noinput')

        self.assertEqual(self.read(self.app_folder, 'package.json'), '[]\n')
        self.assertIn('package.json holds no JSON object.', output)

    def test_upgrade__overwrites_package_file_and_reports_it__when_it_was_edited(self):
        self.run_upgrade('--noinput')
        self.write('// edited\n', self.framework_folder, 'controller.ts')

        output = self.run_upgrade('--noinput')

        self.assertEqual(
            self.read(self.framework_folder, 'controller.ts'),
            self.read(PACKAGE_DIR, 'frontend', 'controller.ts'))
        self.assertIn('changed    controller.ts', output)
        self.assertNotIn('app.ts', output)

    def test_upgrade__leaves_other_files_alone__when_they_are_in_or_beside_the_folder(self):
        self.write('// mine\n', self.framework_folder, 'my_helper.ts')
        self.write('// main\n', self.app_folder, 'ts', 'main.ts')

        self.run_upgrade('--noinput')

        self.assertEqual(self.read(self.framework_folder, 'my_helper.ts'), '// mine\n')
        self.assertEqual(self.read(self.app_folder, 'ts', 'main.ts'), '// main\n')

    def test_upgrade__deletes_file_and_reports_it__when_previous_list_has_a_file_no_longer_shipped(self):
        self.run_upgrade('--noinput')
        readme_path = os.path.join(self.docs_folder, 'README.md')
        readme = self.read(readme_path)
        self.write(readme.replace('- `README.md`', '- `retired.md`\n- `README.md`'), readme_path)
        self.write('# Retired\n', self.docs_folder, 'retired.md')

        output = self.run_upgrade('--noinput')

        self.assertFalse(os.path.exists(os.path.join(self.docs_folder, 'retired.md')))
        self.assertIn('removed    retired.md (no longer shipped)', output)

    def test_upgrade__keeps_file__when_previous_list_names_a_path_outside_the_folder(self):
        self.run_upgrade('--noinput')
        readme_path = os.path.join(self.framework_folder, 'README.md')
        readme = self.read(readme_path)
        self.write(readme.replace('- `README.md`', '- `../main.ts`\n- `README.md`'), readme_path)
        self.write('// main\n', self.app_folder, 'ts', 'main.ts')

        self.run_upgrade('--noinput')

        self.assertTrue(os.path.isfile(os.path.join(self.app_folder, 'ts', 'main.ts')))

    def test_upgrade__reports_up_to_date__when_rerun_with_nothing_changed(self):
        self.run_upgrade('--noinput')

        output = self.run_upgrade('--noinput')

        self.assertIn('is already up to date', output)

    def test_upgrade__suggests_committing_the_folder__when_files_change(self):
        output = self.run_upgrade('--noinput')

        self.assertIn('Commit ', output)
        self.assertIn('added      app.ts', output)

    def test_upgrade__creates_build_files__when_missing(self):
        output = self.run_upgrade('--noinput')

        for filename in (*StarterSite.BUILD_CONFIGS, StarterSite.PACKAGE_JSON):
            with self.subTest(filename=filename):
                self.assertEqual(self.read(self.app_folder, filename), StarterSite('website').file(filename))
                self.assertIn(f'Created website/{filename}', output.replace(self.project_root + os.sep, ''))

    def test_upgrade__creates_none_of_the_other_starter_files__when_app_never_ran_create_app(self):
        self.run_upgrade('--noinput')

        created = set()
        for folder, subfolders, filenames in os.walk(self.app_folder):
            # The managed folders are the package's, so they aren't starter files.
            subfolders[:] = [
                subfolder
                for subfolder in subfolders
                if subfolder not in ('website_widgets', 'website_widgets_docs')
            ]
            for filename in filenames:
                created.add(os.path.relpath(os.path.join(folder, filename), self.app_folder))
        self.assertEqual(created, {*StarterSite.BUILD_CONFIGS, StarterSite.PACKAGE_JSON})

    def test_upgrade__asks_nothing_and_says_nothing__when_build_configs_match_the_starter(self):
        self.run_upgrade('--noinput')

        output = self.run_upgrade(answers=['n'])

        self.assertNotIn('webpack.config.js', output)
        self.assertEqual(len(self.questions), 1)
        self.assertIn('AGENTS.md', self.questions[0])

    def test_upgrade__keeps_edited_webpack_config__when_answer_is_the_default(self):
        self.write('// tuned\n', self.app_folder, 'webpack.config.js')

        output = self.run_upgrade(answers=['', 'n'])

        self.assertEqual(self.read(self.app_folder, 'webpack.config.js'), '// tuned\n')
        self.assertIn('webpack.config.js differs from the starter site', self.questions[0])
        self.assertIn('Kept ', output)

    def test_upgrade__replaces_edited_webpack_config__when_answer_is_yes(self):
        self.write('// tuned\n', self.app_folder, 'webpack.config.js')

        self.run_upgrade(answers=['y', 'n'])

        self.assertEqual(
            self.read(self.app_folder, 'webpack.config.js'),
            StarterSite('website').file('webpack.config.js'))

    def test_upgrade__shows_diff_then_asks_again__when_answer_is_d(self):
        self.write('// tuned\n', self.app_folder, 'webpack.config.js')

        output = self.run_upgrade(answers=['d', 'n', 'n'])

        self.assertIn('-// tuned', output)
        self.assertIn("+const MiniCssExtractPlugin = require('mini-css-extract-plugin');", output)
        self.assertTrue(self.questions[1].startswith('Replace '))
        self.assertEqual(self.read(self.app_folder, 'webpack.config.js'), '// tuned\n')

    def test_upgrade__keeps_edited_tsconfig_without_asking__when_noinput(self):
        self.write('{}\n', self.app_folder, 'tsconfig.json')

        output = self.run_upgrade('--noinput')

        self.assertEqual(self.read(self.app_folder, 'tsconfig.json'), '{}\n')
        self.assertIn('which differs from the starter site', output)

    def test_upgrade__prints_install_command_and_leaves_package_json__when_dependency_is_missing_or_too_low(self):
        starter = json.loads(StarterSite('website').file('package.json'))
        del starter['devDependencies']['ts-loader']
        starter['devDependencies']['webpack'] = '^5.97.1'
        starter['dependencies'] = {'chart.js': '^4.5.0'}
        package_json = json.dumps(starter, indent=2)
        self.write(package_json, self.app_folder, 'package.json')

        output = self.run_upgrade('--noinput')

        self.assertEqual(self.read(self.app_folder, 'package.json'), package_json)
        self.assertIn('npm install --save-dev ts-loader@^9.6.2 webpack@^5.110.2', output)
        self.assertNotIn('chart.js', output)

    def test_upgrade__prints_script_line__when_package_json_lacks_watch(self):
        starter = json.loads(StarterSite('website').file('package.json'))
        del starter['scripts']['watch']
        self.write(json.dumps(starter), self.app_folder, 'package.json')

        output = self.run_upgrade('--noinput')

        self.assertIn('"watch": "webpack --watch"', output)
        self.assertNotIn('npm install', output)

    def test_upgrade__fails_naming_the_label__when_website_app_is_not_installed(self):
        self.mock_apps.get_app_config.side_effect = LookupError

        with self.assertRaisesMessage(CommandError, "'website'"):
            self.run_upgrade('--noinput')

    def test_upgrade__appends_docs_pointer__when_claude_md_exists_and_answer_is_yes(self):
        self.write('# Project\n', self.project_root, 'CLAUDE.md')

        self.run_upgrade(answers=['y'])

        claude_md = self.read(self.project_root, 'CLAUDE.md')
        self.assertTrue(claude_md.startswith('# Project\n'))
        self.assertIn(
            '- `website/website_widgets_docs/AGENTS.md` — how django-website-widgets works; read before '
            'changing pages, widgets or controllers\n',
            claude_md)

    def test_upgrade__leaves_claude_md_alone__when_answer_is_the_default(self):
        self.write('# Project\n', self.project_root, 'CLAUDE.md')

        self.run_upgrade(answers=[''])

        self.assertEqual(self.read(self.project_root, 'CLAUDE.md'), '# Project\n')

    def test_upgrade__asks_nothing__when_claude_md_already_points_at_the_docs(self):
        self.write('See `website/website_widgets_docs/AGENTS.md`.\n', self.project_root, 'CLAUDE.md')

        self.run_upgrade()

        self.assertEqual(self.questions, [])

    def test_upgrade__appends_docs_pointer__when_only_dot_claude_claude_md_exists_and_answer_is_yes(self):
        self.write('# Project\n', self.project_root, '.claude', 'CLAUDE.md')

        self.run_upgrade(answers=['y'])

        self.assertIn('.claude/CLAUDE.md', self.questions[0])
        self.assertIn('website/website_widgets_docs/AGENTS.md', self.read(self.project_root, '.claude', 'CLAUDE.md'))
        self.assertFalse(os.path.exists(os.path.join(self.project_root, 'AGENTS.md')))

    def test_upgrade__asks_once_per_file__when_every_assistant_file_exists(self):
        self.write('# Claude\n', self.project_root, 'CLAUDE.md')
        self.write('# Dot Claude\n', self.project_root, '.claude', 'CLAUDE.md')
        self.write('# Agents\n', self.project_root, 'AGENTS.md')

        self.run_upgrade(answers=['n', 'n', 'y'])

        self.assertEqual(
            [question.split()[4] for question in self.questions],
            ['CLAUDE.md', '.claude/CLAUDE.md', 'AGENTS.md'])
        self.assertEqual(self.read(self.project_root, 'CLAUDE.md'), '# Claude\n')
        self.assertEqual(self.read(self.project_root, '.claude', 'CLAUDE.md'), '# Dot Claude\n')
        self.assertIn('website/website_widgets_docs/AGENTS.md', self.read(self.project_root, 'AGENTS.md'))

    def test_upgrade__creates_agents_md__when_neither_file_exists_and_answer_is_yes(self):
        self.run_upgrade(answers=['y'])

        self.assertIn('website/website_widgets_docs/AGENTS.md', self.read(self.project_root, 'AGENTS.md'))

    def test_upgrade__updates_the_pre_0_8_0_pointer_in_place__when_answer_is_yes(self):
        claude_md = (
            '# Project\n'
            f'{OLD_POINTER_LINE}\n'
            '- `docs/other.md` — something else\n')
        self.write(claude_md, self.project_root, 'CLAUDE.md')

        output = self.run_upgrade(answers=['y'])

        self.assertEqual(len(self.questions), 1)
        self.assertIn('which moved to website/website_widgets_docs/AGENTS.md', self.questions[0])
        self.assertEqual(
            self.read(self.project_root, 'CLAUDE.md'),
            claude_md.replace('website/ts/website_widgets/AGENTS.md', 'website/website_widgets_docs/AGENTS.md'))
        self.assertIn('Updated the pointer in CLAUDE.md.', output)

    def test_upgrade__leaves_the_pre_0_8_0_pointer__when_answer_is_the_default(self):
        claude_md = f'# Project\n{OLD_POINTER_LINE}\n'
        self.write(claude_md, self.project_root, 'CLAUDE.md')

        self.run_upgrade(answers=[''])

        self.assertEqual(self.read(self.project_root, 'CLAUDE.md'), claude_md)

    def test_upgrade__says_the_pointer_moved_without_changing_it__when_noinput(self):
        claude_md = f'# Project\n{OLD_POINTER_LINE}\n'
        self.write(claude_md, self.project_root, 'CLAUDE.md')

        output = self.run_upgrade('--noinput')

        self.assertEqual(self.read(self.project_root, 'CLAUDE.md'), claude_md)
        self.assertIn('CLAUDE.md points to website/ts/website_widgets/AGENTS.md, which moved', output)

    def test_upgrade__asks_once__when_claude_md_is_a_link_to_agents_md(self):
        self.write('# Agents\n', self.project_root, 'AGENTS.md')
        os.symlink('AGENTS.md', os.path.join(self.project_root, 'CLAUDE.md'))

        self.run_upgrade(answers=['n'])

        self.assertEqual(len(self.questions), 1)

    def test_upgrade__adds_no_pointer_and_says_so__when_noinput(self):
        self.write('# Project\n', self.project_root, 'CLAUDE.md')

        output = self.run_upgrade('--noinput')

        self.assertEqual(self.questions, [])
        self.assertEqual(self.read(self.project_root, 'CLAUDE.md'), '# Project\n')
        self.assertIn('rerun without --noinput', output)
