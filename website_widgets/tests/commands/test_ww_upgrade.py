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
from website_widgets.management.npm_package import NpmPackage
from website_widgets.management.starter_site import StarterSite


PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The pointer 0.7.0's commands added, before the docs moved out of ts/website_widgets/.
OLD_POINTER_LINE = (
    '- `website/ts/website_widgets/AGENTS.md` — how django-website-widgets works; read before '
    'changing pages, widgets or controllers')

# The pointer ww_upgrade adds to an assistant file.
DOCS_POINTER_LINE = (
    '- `website/website_widgets_docs/AGENTS.md` — how django-website-widgets works; read before '
    'changing pages, widgets or controllers\n')


class WwUpgradeTestCase(SimpleTestCase):
    """The website app and the project root are temp folders; no real project is touched."""

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.project_root = temp_dir.name
        self.app_folder = os.path.join(self.project_root, 'website')
        self.docs_folder = os.path.join(self.app_folder, 'website_widgets_docs')
        os.makedirs(self.app_folder)
        self.starter_site = StarterSite('website')

        app_config = SimpleNamespace(path=self.app_folder)
        self.mock_apps = self.enterContext(patch('website_widgets.management.commands.ww_upgrade.apps'))
        self.mock_apps.get_app_config.return_value = app_config

    def run_upgrade(
        self,
        *args,
        answers: list[str] | type[EOFError] | None = None
    ) -> str:
        """`answers` are typed in turn; `EOFError` stands for a closed stdin, as in a script."""
        output = io.StringIO()
        input_answers = answers or []
        with patch('builtins.input', side_effect=input_answers) as mock_input:
            call_command('ww_upgrade', '--project-root', self.project_root, *args, stdout=output, no_color=True)
        self.questions = [
            input_call.args[0]
            for input_call in mock_input.call_args_list
        ]
        return output.getvalue()

    def read(self, *path_parts: str) -> str:
        file_path = os.path.join(*path_parts)
        with open(file_path, encoding='utf-8') as file:
            return file.read()

    def write(self, content: str, *path_parts: str):
        file_path = os.path.join(*path_parts)
        folder = os.path.dirname(file_path)
        os.makedirs(folder, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)

    def read_starter_package_json(self) -> dict:
        starter_package_json = self.starter_site.file('package.json')
        return json.loads(starter_package_json)

    def add_to_previous_file_list(self, line: str):
        """Lists `line` in the docs folder's README, as if an earlier version had shipped it."""
        readme_path = os.path.join(self.docs_folder, 'README.md')
        readme = self.read(readme_path)
        edited_readme = readme.replace('- `README.md`', f'{line}\n- `README.md`')
        self.write(edited_readme, readme_path)

    def test_upgrade__writes_docs_into_their_folder__when_folder_is_missing(self):
        self.run_upgrade('--noinput')

        copied_agents_md = self.read(self.docs_folder, 'AGENTS.md')
        package_agents_md = self.read(PACKAGE_DIR, 'docs', 'AGENTS.md')
        copied_routing_md = self.read(self.docs_folder, 'routing.md')
        package_routing_md = self.read(PACKAGE_DIR, 'docs', 'routing.md')
        nested_docs_folder = os.path.join(self.docs_folder, 'docs')
        nested_docs_folder_exists = os.path.exists(nested_docs_folder)
        self.assertEqual(copied_agents_md, package_agents_md)
        self.assertEqual(copied_routing_md, package_routing_md)
        self.assertFalse(nested_docs_folder_exists)

    def test_upgrade__stamps_readme_with_version_and_its_files__when_run(self):
        self.run_upgrade('--noinput')

        version = importlib.metadata.version('django-website-widgets')
        readme = self.read(self.docs_folder, 'README.md')
        self.assertIn(version, readme)
        for path in ('AGENTS.md', 'routing.md', 'README.md'):
            with self.subTest(path=path):
                self.assertIn(f'- `{path}`', readme)

    def test_upgrade__restores_a_package_file__when_it_was_deleted(self):
        self.run_upgrade('--noinput')
        routing_path = os.path.join(self.docs_folder, 'routing.md')
        os.remove(routing_path)

        output = self.run_upgrade('--noinput')

        copied_routing_md = self.read(routing_path)
        package_routing_md = self.read(PACKAGE_DIR, 'docs', 'routing.md')
        self.assertEqual(copied_routing_md, package_routing_md)
        self.assertIn('added      routing.md', output)

    def test_upgrade__leaves_package_file_alone__when_it_differs_only_in_line_endings(self):
        self.run_upgrade('--noinput')
        routing_path = os.path.join(self.docs_folder, 'routing.md')
        package_routing_md = self.read(PACKAGE_DIR, 'docs', 'routing.md')
        crlf_content = package_routing_md.replace('\n', '\r\n')
        with open(routing_path, 'w', encoding='utf-8', newline='') as file:
            file.write(crlf_content)

        output = self.run_upgrade('--noinput')

        with open(routing_path, encoding='utf-8', newline='') as file:
            routing_md = file.read()
        self.assertIn('website_widgets_docs/ is already up to date', output)
        self.assertEqual(routing_md, crlf_content)

    def test_upgrade__runs_no_system_checks__when_run_from_manage_py(self):
        # call_command() skips the checks for every command, so this runs it the way manage.py does.
        argv = ['manage.py', 'ww_upgrade', '--noinput', '--project-root', self.project_root]
        command = ww_upgrade.Command()
        discarded_output = io.StringIO()

        with patch('django.core.checks.run_checks') as mock_run_checks, contextlib.redirect_stdout(discarded_output):
            command.run_from_argv(argv)

        mock_run_checks.assert_not_called()

    def test_upgrade__keeps_edited_webpack_config_and_asks_nothing_more__when_there_is_no_input_to_read(self):
        self.write('// tuned\n', self.app_folder, 'webpack.config.js')
        self.write('# Project\n', self.project_root, 'CLAUDE.md')

        output = self.run_upgrade(answers=EOFError)

        webpack_config = self.read(self.app_folder, 'webpack.config.js')
        claude_md = self.read(self.project_root, 'CLAUDE.md')
        self.assertEqual(webpack_config, '// tuned\n')
        self.assertEqual(claude_md, '# Project\n')
        self.assertIn('Kept ', output)

    def test_upgrade__prints_the_error_and_leaves_package_json__when_it_is_not_a_json_object(self):
        self.write('[]\n', self.app_folder, 'package.json')

        output = self.run_upgrade('--noinput')

        package_json = self.read(self.app_folder, 'package.json')
        self.assertEqual(package_json, '[]\n')
        self.assertIn('package.json holds no JSON object.', output)

    def test_upgrade__overwrites_package_file_and_reports_it__when_it_was_edited(self):
        self.run_upgrade('--noinput')
        self.write('# edited\n', self.docs_folder, 'routing.md')

        output = self.run_upgrade('--noinput')

        copied_routing_md = self.read(self.docs_folder, 'routing.md')
        package_routing_md = self.read(PACKAGE_DIR, 'docs', 'routing.md')
        self.assertEqual(copied_routing_md, package_routing_md)
        self.assertIn('changed    routing.md', output)
        self.assertNotIn('changed    AGENTS.md', output)

    def test_upgrade__leaves_other_files_alone__when_they_are_in_or_beside_the_folder(self):
        self.write('# mine\n', self.docs_folder, 'my_notes.md')
        self.write('// main\n', self.app_folder, 'ts', 'main.ts')

        self.run_upgrade('--noinput')

        my_notes = self.read(self.docs_folder, 'my_notes.md')
        main_ts = self.read(self.app_folder, 'ts', 'main.ts')
        self.assertEqual(my_notes, '# mine\n')
        self.assertEqual(main_ts, '// main\n')

    def test_upgrade__deletes_file_and_reports_it__when_previous_list_has_a_file_no_longer_shipped(self):
        self.run_upgrade('--noinput')
        self.add_to_previous_file_list('- `retired.md`')
        self.write('# Retired\n', self.docs_folder, 'retired.md')

        output = self.run_upgrade('--noinput')

        retired_path = os.path.join(self.docs_folder, 'retired.md')
        retired_exists = os.path.exists(retired_path)
        self.assertFalse(retired_exists)
        self.assertIn('removed    retired.md (no longer shipped)', output)

    def test_upgrade__keeps_file__when_previous_list_names_a_path_outside_the_folder(self):
        self.run_upgrade('--noinput')
        self.add_to_previous_file_list('- `../ts/main.ts`')
        self.write('// main\n', self.app_folder, 'ts', 'main.ts')

        self.run_upgrade('--noinput')

        main_ts_path = os.path.join(self.app_folder, 'ts', 'main.ts')
        main_ts_exists = os.path.isfile(main_ts_path)
        self.assertTrue(main_ts_exists)

    def test_upgrade__reports_up_to_date__when_rerun_with_nothing_changed(self):
        self.run_upgrade('--noinput')

        output = self.run_upgrade('--noinput')

        self.assertIn('is already up to date', output)

    def test_upgrade__suggests_committing_the_folder__when_files_change(self):
        output = self.run_upgrade('--noinput')

        self.assertIn('Commit ', output)
        self.assertIn('added      AGENTS.md', output)

    def test_upgrade__creates_build_files__when_missing(self):
        output = self.run_upgrade('--noinput')

        relative_output = output.replace(self.project_root + os.sep, '')
        for filename in (*StarterSite.BUILD_CONFIGS, StarterSite.PACKAGE_JSON):
            with self.subTest(filename=filename):
                created = self.read(self.app_folder, filename)
                starter = self.starter_site.file(filename)
                self.assertEqual(created, starter)
                self.assertIn(f'Created website/{filename}', relative_output)

    def test_upgrade__creates_none_of_the_other_starter_files__when_app_never_ran_create_app(self):
        self.run_upgrade('--noinput')

        created = set()
        for folder, subfolders, filenames in os.walk(self.app_folder):
            # The managed folder is the package's, so it isn't starter files.
            subfolders[:] = [
                subfolder
                for subfolder in subfolders
                if subfolder != 'website_widgets_docs'
            ]
            for filename in filenames:
                file_path = os.path.join(folder, filename)
                relative_path = os.path.relpath(file_path, self.app_folder)
                created.add(relative_path)
        expected_created = {*StarterSite.BUILD_CONFIGS, StarterSite.PACKAGE_JSON}
        self.assertEqual(created, expected_created)

    def test_upgrade__asks_nothing_and_says_nothing__when_build_configs_match_the_starter(self):
        self.run_upgrade('--noinput')

        output = self.run_upgrade(answers=['n'])

        self.assertNotIn('webpack.config.js', output)
        self.assertEqual(len(self.questions), 1)
        self.assertIn('AGENTS.md', self.questions[0])

    def test_upgrade__keeps_edited_webpack_config__when_answer_is_the_default(self):
        self.write('// tuned\n', self.app_folder, 'webpack.config.js')

        output = self.run_upgrade(answers=['', 'n'])

        webpack_config = self.read(self.app_folder, 'webpack.config.js')
        self.assertEqual(webpack_config, '// tuned\n')
        self.assertIn('webpack.config.js differs from the starter site', self.questions[0])
        self.assertIn('Kept ', output)

    def test_upgrade__replaces_edited_webpack_config__when_answer_is_yes(self):
        self.write('// tuned\n', self.app_folder, 'webpack.config.js')

        self.run_upgrade(answers=['y', 'n'])

        webpack_config = self.read(self.app_folder, 'webpack.config.js')
        starter_webpack_config = self.starter_site.file('webpack.config.js')
        self.assertEqual(webpack_config, starter_webpack_config)

    def test_upgrade__shows_diff_then_asks_again__when_answer_is_d(self):
        self.write('// tuned\n', self.app_folder, 'webpack.config.js')

        output = self.run_upgrade(answers=['d', 'n', 'n'])

        asked_to_replace = self.questions[1].startswith('Replace ')
        webpack_config = self.read(self.app_folder, 'webpack.config.js')
        self.assertIn('-// tuned', output)
        self.assertIn("+const MiniCssExtractPlugin = require('mini-css-extract-plugin');", output)
        self.assertTrue(asked_to_replace)
        self.assertEqual(webpack_config, '// tuned\n')

    def test_upgrade__keeps_edited_tsconfig_without_asking__when_noinput(self):
        self.write('{}\n', self.app_folder, 'tsconfig.json')

        output = self.run_upgrade('--noinput')

        tsconfig = self.read(self.app_folder, 'tsconfig.json')
        self.assertEqual(tsconfig, '{}\n')
        self.assertIn('which differs from the starter site', output)

    def test_upgrade__prints_install_command_and_leaves_package_json__when_dependency_is_missing_or_too_low(self):
        starter = self.read_starter_package_json()
        del starter['devDependencies']['ts-loader']
        starter['devDependencies']['webpack'] = '^5.97.1'
        starter['dependencies']['chart.js'] = '^4.5.0'
        package_json = json.dumps(starter, indent=2)
        self.write(package_json, self.app_folder, 'package.json')

        output = self.run_upgrade('--noinput')

        package_json_after = self.read(self.app_folder, 'package.json')
        self.assertEqual(package_json_after, package_json)
        self.assertIn('npm install --save-dev ts-loader@^9.6.2 webpack@^5.110.2', output)
        self.assertNotIn('chart.js', output)

    def test_upgrade__sets_the_npm_range_and_keeps_the_rest__when_package_json_asks_for_an_older_one(self):
        starter = self.read_starter_package_json()
        starter['dependencies'][NpmPackage.NAME] = '^0.9.0'
        package_json = json.dumps(starter, indent=4)
        self.write(package_json, self.app_folder, 'package.json')

        output = self.run_upgrade('--noinput')

        package_json_after = self.read(self.app_folder, 'package.json')
        expected = package_json.replace('"^0.9.0"', f'"{NpmPackage.RANGE}"')
        self.assertEqual(package_json_after, expected)
        self.assertIn(f'Set {NpmPackage.NAME} to "{NpmPackage.RANGE}"', output)

    def test_upgrade__adds_the_npm_range_to_dependencies__when_package_json_lacks_it(self):
        starter = self.read_starter_package_json()
        del starter['dependencies'][NpmPackage.NAME]
        package_json_text = json.dumps(starter, indent=2)
        self.write(package_json_text, self.app_folder, 'package.json')

        self.run_upgrade('--noinput')

        package_json_after_text = self.read(self.app_folder, 'package.json')
        package_json_after = json.loads(package_json_after_text)
        npm_package_range = package_json_after['dependencies'][NpmPackage.NAME]
        self.assertEqual(npm_package_range, NpmPackage.RANGE)
        self.assertEqual(package_json_after['devDependencies'], starter['devDependencies'])

    def test_upgrade__leaves_package_json_alone__when_npm_package_is_a_local_folder(self):
        starter = self.read_starter_package_json()
        starter['dependencies'][NpmPackage.NAME] = 'file:../../../frontend'
        package_json = json.dumps(starter, indent=2)
        self.write(package_json, self.app_folder, 'package.json')

        output = self.run_upgrade('--noinput')

        package_json_after = self.read(self.app_folder, 'package.json')
        self.assertEqual(package_json_after, package_json)
        self.assertNotIn(f'Set {NpmPackage.NAME}', output)

    def test_upgrade__prints_script_line__when_package_json_lacks_watch(self):
        starter = self.read_starter_package_json()
        del starter['scripts']['watch']
        package_json = json.dumps(starter)
        self.write(package_json, self.app_folder, 'package.json')

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
        keeps_its_start = claude_md.startswith('# Project\n')
        self.assertTrue(keeps_its_start)
        self.assertIn(DOCS_POINTER_LINE, claude_md)

    def test_upgrade__leaves_claude_md_alone__when_answer_is_the_default(self):
        self.write('# Project\n', self.project_root, 'CLAUDE.md')

        self.run_upgrade(answers=[''])

        claude_md = self.read(self.project_root, 'CLAUDE.md')
        self.assertEqual(claude_md, '# Project\n')

    def test_upgrade__asks_nothing__when_claude_md_already_points_at_the_docs(self):
        self.write('See `website/website_widgets_docs/AGENTS.md`.\n', self.project_root, 'CLAUDE.md')

        self.run_upgrade()

        self.assertEqual(self.questions, [])

    def test_upgrade__appends_docs_pointer__when_only_dot_claude_claude_md_exists_and_answer_is_yes(self):
        self.write('# Project\n', self.project_root, '.claude', 'CLAUDE.md')

        self.run_upgrade(answers=['y'])

        dot_claude_md = self.read(self.project_root, '.claude', 'CLAUDE.md')
        agents_md_path = os.path.join(self.project_root, 'AGENTS.md')
        agents_md_exists = os.path.exists(agents_md_path)
        self.assertIn('.claude/CLAUDE.md', self.questions[0])
        self.assertIn('website/website_widgets_docs/AGENTS.md', dot_claude_md)
        self.assertFalse(agents_md_exists)

    def test_upgrade__asks_once_per_file__when_every_assistant_file_exists(self):
        self.write('# Claude\n', self.project_root, 'CLAUDE.md')
        self.write('# Dot Claude\n', self.project_root, '.claude', 'CLAUDE.md')
        self.write('# Agents\n', self.project_root, 'AGENTS.md')

        self.run_upgrade(answers=['n', 'n', 'y'])

        asked_files = [
            question.split()[4]
            for question in self.questions
        ]
        claude_md = self.read(self.project_root, 'CLAUDE.md')
        dot_claude_md = self.read(self.project_root, '.claude', 'CLAUDE.md')
        agents_md = self.read(self.project_root, 'AGENTS.md')
        self.assertEqual(asked_files, ['CLAUDE.md', '.claude/CLAUDE.md', 'AGENTS.md'])
        self.assertEqual(claude_md, '# Claude\n')
        self.assertEqual(dot_claude_md, '# Dot Claude\n')
        self.assertIn('website/website_widgets_docs/AGENTS.md', agents_md)

    def test_upgrade__creates_agents_md__when_neither_file_exists_and_answer_is_yes(self):
        self.run_upgrade(answers=['y'])

        agents_md = self.read(self.project_root, 'AGENTS.md')
        self.assertIn('website/website_widgets_docs/AGENTS.md', agents_md)

    def test_upgrade__updates_the_pre_0_8_0_pointer_in_place__when_answer_is_yes(self):
        claude_md = (
            '# Project\n'
            f'{OLD_POINTER_LINE}\n'
            '- `docs/other.md` — something else\n')
        self.write(claude_md, self.project_root, 'CLAUDE.md')

        output = self.run_upgrade(answers=['y'])

        claude_md_after = self.read(self.project_root, 'CLAUDE.md')
        expected = claude_md.replace('website/ts/website_widgets/AGENTS.md', 'website/website_widgets_docs/AGENTS.md')
        self.assertEqual(len(self.questions), 1)
        self.assertIn('which moved to website/website_widgets_docs/AGENTS.md', self.questions[0])
        self.assertEqual(claude_md_after, expected)
        self.assertIn('Updated the pointer in CLAUDE.md.', output)

    def test_upgrade__leaves_the_pre_0_8_0_pointer__when_answer_is_the_default(self):
        claude_md = f'# Project\n{OLD_POINTER_LINE}\n'
        self.write(claude_md, self.project_root, 'CLAUDE.md')

        self.run_upgrade(answers=[''])

        claude_md_after = self.read(self.project_root, 'CLAUDE.md')
        self.assertEqual(claude_md_after, claude_md)

    def test_upgrade__says_the_pointer_moved_without_changing_it__when_noinput(self):
        claude_md = f'# Project\n{OLD_POINTER_LINE}\n'
        self.write(claude_md, self.project_root, 'CLAUDE.md')

        output = self.run_upgrade('--noinput')

        claude_md_after = self.read(self.project_root, 'CLAUDE.md')
        self.assertEqual(claude_md_after, claude_md)
        self.assertIn('CLAUDE.md points to website/ts/website_widgets/AGENTS.md, which moved', output)

    def test_upgrade__asks_once__when_claude_md_is_a_link_to_agents_md(self):
        self.write('# Agents\n', self.project_root, 'AGENTS.md')
        claude_md_path = os.path.join(self.project_root, 'CLAUDE.md')
        os.symlink('AGENTS.md', claude_md_path)

        self.run_upgrade(answers=['n'])

        self.assertEqual(len(self.questions), 1)

    def test_upgrade__adds_no_pointer_and_says_so__when_noinput(self):
        self.write('# Project\n', self.project_root, 'CLAUDE.md')

        output = self.run_upgrade('--noinput')

        claude_md = self.read(self.project_root, 'CLAUDE.md')
        self.assertEqual(self.questions, [])
        self.assertEqual(claude_md, '# Project\n')
        self.assertIn('rerun without --noinput', output)
