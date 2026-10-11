import importlib.metadata
import io
import os
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase


PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class InitWebsiteWidgetsTestCase(SimpleTestCase):
    """The website app and the project root are temp folders; no real project is touched."""

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.project_root = temp_dir.name
        self.app_folder = os.path.join(self.project_root, 'website')
        self.framework_folder = os.path.join(self.app_folder, 'ts', 'website_widgets')
        os.makedirs(self.app_folder)

        mock_apps = self.enterContext(patch('website_widgets.management.commands.init_website_widgets.apps'))
        mock_apps.get_app_config.return_value = SimpleNamespace(path=self.app_folder)
        self.mock_apps = mock_apps

    def run_init(self, *args, answers: list[str] | None = None) -> str:
        output = io.StringIO()
        with patch('builtins.input', side_effect=answers or []) as mock_input:
            call_command('init_website_widgets', '--project-root', self.project_root, *args, stdout=output)
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

    def test_init__writes_framework_typescript_and_docs__when_folder_is_missing(self):
        self.run_init('--noinput')

        self.assertEqual(
            self.read(self.framework_folder, 'controller.ts'),
            self.read(PACKAGE_DIR, 'frontend', 'controller.ts'))
        self.assertEqual(
            self.read(self.framework_folder, 'AGENTS.md'),
            self.read(PACKAGE_DIR, 'AGENTS.md'))
        self.assertEqual(
            self.read(self.framework_folder, 'docs', 'routing.md'),
            self.read(PACKAGE_DIR, 'docs', 'routing.md'))

    def test_init__stamps_readme_with_version_and_every_file__when_run(self):
        self.run_init('--noinput')

        readme = self.read(self.framework_folder, 'README.md')
        self.assertIn(importlib.metadata.version('django-website-widgets'), readme)
        for path in ('app.ts', 'controller.ts', 'completer.ts', 'AGENTS.md', 'docs/routing.md', 'README.md'):
            with self.subTest(path=path):
                self.assertIn(f'- `{path}`', readme)

    def test_init__overwrites_package_file_and_reports_it__when_it_was_edited(self):
        self.run_init('--noinput')
        self.write('// edited\n', self.framework_folder, 'controller.ts')

        output = self.run_init('--noinput')

        self.assertEqual(
            self.read(self.framework_folder, 'controller.ts'),
            self.read(PACKAGE_DIR, 'frontend', 'controller.ts'))
        self.assertIn('changed    controller.ts', output)
        self.assertNotIn('app.ts', output)

    def test_init__leaves_other_files_alone__when_they_are_in_or_beside_the_folder(self):
        self.write('// mine\n', self.framework_folder, 'my_helper.ts')
        self.write('// main\n', self.app_folder, 'ts', 'main.ts')

        self.run_init('--noinput')

        self.assertEqual(self.read(self.framework_folder, 'my_helper.ts'), '// mine\n')
        self.assertEqual(self.read(self.app_folder, 'ts', 'main.ts'), '// main\n')

    def test_init__deletes_file_and_reports_it__when_previous_list_has_a_file_no_longer_shipped(self):
        self.run_init('--noinput')
        readme_path = os.path.join(self.framework_folder, 'README.md')
        readme = self.read(readme_path)
        self.write(readme.replace('- `README.md`', '- `docs/retired.md`\n- `README.md`'), readme_path)
        self.write('# Retired\n', self.framework_folder, 'docs', 'retired.md')

        output = self.run_init('--noinput')

        self.assertFalse(os.path.exists(os.path.join(self.framework_folder, 'docs', 'retired.md')))
        self.assertIn('removed    docs/retired.md (no longer shipped)', output)

    def test_init__keeps_file__when_previous_list_names_a_path_outside_the_folder(self):
        self.run_init('--noinput')
        readme_path = os.path.join(self.framework_folder, 'README.md')
        readme = self.read(readme_path)
        self.write(readme.replace('- `README.md`', '- `../main.ts`\n- `README.md`'), readme_path)
        self.write('// main\n', self.app_folder, 'ts', 'main.ts')

        self.run_init('--noinput')

        self.assertTrue(os.path.isfile(os.path.join(self.app_folder, 'ts', 'main.ts')))

    def test_init__reports_up_to_date__when_rerun_with_nothing_changed(self):
        self.run_init('--noinput')

        output = self.run_init('--noinput')

        self.assertIn('is already up to date', output)

    def test_init__suggests_committing_the_folder__when_files_change(self):
        output = self.run_init('--noinput')

        self.assertIn('Commit ', output)
        self.assertIn('added      app.ts', output)

    def test_init__fails_naming_the_label__when_website_app_is_not_installed(self):
        self.mock_apps.get_app_config.side_effect = LookupError

        with self.assertRaisesMessage(CommandError, "'website'"):
            self.run_init('--noinput')

    def test_init__appends_docs_pointer__when_claude_md_exists_and_answer_is_yes(self):
        self.write('# Project\n', self.project_root, 'CLAUDE.md')

        self.run_init(answers=['y'])

        claude_md = self.read(self.project_root, 'CLAUDE.md')
        self.assertTrue(claude_md.startswith('# Project\n'))
        self.assertIn(
            '- `website/ts/website_widgets/AGENTS.md` — how django-website-widgets works; read before '
            'changing pages, widgets or controllers\n',
            claude_md)

    def test_init__leaves_claude_md_alone__when_answer_is_the_default(self):
        self.write('# Project\n', self.project_root, 'CLAUDE.md')

        self.run_init(answers=[''])

        self.assertEqual(self.read(self.project_root, 'CLAUDE.md'), '# Project\n')

    def test_init__asks_nothing__when_claude_md_already_points_at_the_docs(self):
        self.write('See `website/ts/website_widgets/AGENTS.md`.\n', self.project_root, 'CLAUDE.md')

        self.run_init()

        self.assertEqual(self.questions, [])

    def test_init__appends_docs_pointer__when_only_dot_claude_claude_md_exists_and_answer_is_yes(self):
        self.write('# Project\n', self.project_root, '.claude', 'CLAUDE.md')

        self.run_init(answers=['y'])

        self.assertIn('.claude/CLAUDE.md', self.questions[0])
        self.assertIn('website/ts/website_widgets/AGENTS.md', self.read(self.project_root, '.claude', 'CLAUDE.md'))
        self.assertFalse(os.path.exists(os.path.join(self.project_root, 'AGENTS.md')))

    def test_init__asks_once_per_file__when_every_assistant_file_exists(self):
        self.write('# Claude\n', self.project_root, 'CLAUDE.md')
        self.write('# Dot Claude\n', self.project_root, '.claude', 'CLAUDE.md')
        self.write('# Agents\n', self.project_root, 'AGENTS.md')

        self.run_init(answers=['n', 'n', 'y'])

        self.assertEqual(
            [question.split()[4] for question in self.questions],
            ['CLAUDE.md', '.claude/CLAUDE.md', 'AGENTS.md'])
        self.assertEqual(self.read(self.project_root, 'CLAUDE.md'), '# Claude\n')
        self.assertEqual(self.read(self.project_root, '.claude', 'CLAUDE.md'), '# Dot Claude\n')
        self.assertIn('website/ts/website_widgets/AGENTS.md', self.read(self.project_root, 'AGENTS.md'))

    def test_init__creates_agents_md__when_neither_file_exists_and_answer_is_yes(self):
        self.run_init(answers=['y'])

        self.assertIn('website/ts/website_widgets/AGENTS.md', self.read(self.project_root, 'AGENTS.md'))

    def test_init__adds_no_pointer_and_says_so__when_noinput(self):
        self.write('# Project\n', self.project_root, 'CLAUDE.md')

        output = self.run_init('--noinput')

        self.assertEqual(self.questions, [])
        self.assertEqual(self.read(self.project_root, 'CLAUDE.md'), '# Project\n')
        self.assertIn('rerun without --noinput', output)
