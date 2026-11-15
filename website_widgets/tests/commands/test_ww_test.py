import io
import json
import os
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import call, patch

from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import SystemCheckError
from django.test import SimpleTestCase

from website_widgets.config import WebsiteWidgetsConfig
from website_widgets.management.commands.ww_test import Command


class WwTestTestCase(SimpleTestCase):
    """
    Nothing is run: `subprocess.run` and `shutil.which` are mocked, the system checks pass unless
    a test says otherwise, the website app is a temp folder, and each test sets the config's build
    command.
    """

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.app_folder = temp_dir.name
        self.mock_apps = self.enterContext(patch('website_widgets.management.commands.ww_test.apps'))
        self.mock_apps.get_app_config.return_value = SimpleNamespace(path=self.app_folder)
        self.config = WebsiteWidgetsConfig()
        self.enterContext(patch(
            'website_widgets.management.commands.ww_test.get_config',
            side_effect=lambda: self.config))
        self.mock_check = self.enterContext(patch.object(Command, 'check'))
        self.mock_run = self.enterContext(patch('website_widgets.management.commands.ww_test.subprocess.run'))
        self.mock_which = self.enterContext(patch('website_widgets.management.commands.ww_test.shutil.which'))
        self.mock_which.side_effect = lambda name: f'/usr/bin/{name}'
        self.return_codes([0, 0, 0])

    def return_codes(self, codes: list[int]):
        self.mock_run.side_effect = [SimpleNamespace(returncode=code) for code in codes]

    def write_package_json(self, scripts: dict | None = None, node_modules: bool = True):
        """A package.json with these scripts (a build and a test script unless given), and node_modules/ unless told not to."""
        if scripts is None:
            scripts = {'build': 'webpack', 'test': 'vitest run'}
        package_json_path = os.path.join(self.app_folder, 'package.json')
        with open(package_json_path, 'w') as package_json_file:
            json.dump({'scripts': scripts}, package_json_file)
        if node_modules:
            node_modules_path = os.path.join(self.app_folder, 'node_modules')
            os.makedirs(node_modules_path)

    def run_command(self, *arguments: str) -> tuple[int, str, str]:
        """Runs `manage.py ww_test <arguments>` and returns its exit code, output and error output."""
        output = io.StringIO()
        error_output = io.StringIO()
        command = Command(stdout=output, stderr=error_output, no_color=True)
        exit_code = 0
        try:
            command.run_from_argv(['manage.py', 'ww_test', *arguments])
        except SystemExit as exit:
            exit_code = exit.code
        return exit_code, output.getvalue(), error_output.getvalue()

    def test_ww_test__builds_then_runs_both_halves__when_the_app_has_a_test_script(self):
        self.write_package_json()

        exit_code, output, _ = self.run_command()

        expected_calls = [
            call(['/usr/bin/npm', 'run', 'build'], cwd=self.app_folder),
            call([sys.executable, 'manage.py', 'test']),
            call(['/usr/bin/npm', 'test'], cwd=self.app_folder),
        ]
        expected_summary = (
            'Build: passed\n'
            'Python tests: passed\n'
            'npm tests: passed'
        )
        self.assertEqual(self.mock_run.call_args_list, expected_calls)
        self.assertEqual(exit_code, 0)
        self.assertIn(expected_summary, output)

    def test_ww_test__heads_each_step_with_its_command__when_it_runs(self):
        self.write_package_json()

        _, output, _ = self.run_command('--exclude-tag=playwright')

        shown_folder = os.path.relpath(self.app_folder) + os.sep
        self.assertIn(f'── Build: npm run build (in {shown_folder})', output)
        self.assertIn('── Python tests: manage.py test --exclude-tag=playwright\n', output)
        self.assertIn(f'── npm tests: npm test (in {shown_folder})', output)

    def test_ww_test__passes_every_other_argument_to_test__when_run_from_manage_py(self):
        self.write_package_json()

        self.run_command('--exclude-tag=playwright', 'website.tests', '-v', '2')

        python_call = self.mock_run.call_args_list[1]
        expected_call = call([sys.executable, 'manage.py', 'test', '--exclude-tag=playwright', 'website.tests', '-v', '2'])
        self.assertEqual(python_call, expected_call)

    def test_ww_test__runs_nothing_and_shows_the_check_errors__when_the_system_checks_fail(self):
        self.mock_check.side_effect = SystemCheckError('website_widgets.E001: the website app is not installed')

        exit_code, output, error_output = self.run_command()

        self.mock_run.assert_not_called()
        self.assertEqual(exit_code, 1)
        self.assertIn('SystemCheckError: website_widgets.E001', error_output)

    def test_ww_test__shows_one_line__when_loading_the_urls_finds_the_setup_wrong(self):
        self.mock_check.side_effect = ImproperlyConfigured('no installed app has that label')

        exit_code, _, error_output = self.run_command()

        self.mock_run.assert_not_called()
        self.assertEqual(exit_code, 1)
        self.assertEqual(error_output, 'ImproperlyConfigured: no installed app has that label\n')

    def test_ww_test__raises_with_the_traceback__when_traceback_given(self):
        self.mock_check.side_effect = ImproperlyConfigured('no installed app has that label')

        with self.assertRaises(ImproperlyConfigured):
            self.run_command('--traceback')

    def test_ww_test__names_the_setting__when_no_installed_app_has_the_label(self):
        self.mock_apps.get_app_config.side_effect = LookupError('No installed app with label')

        exit_code, _, error_output = self.run_command()

        self.mock_run.assert_not_called()
        self.assertEqual(exit_code, 1)
        self.assertIn("website_app_name is 'website', but no installed app has that label", error_output)

    def test_ww_test__runs_the_configured_build_command__when_one_is_set(self):
        self.config = WebsiteWidgetsConfig(test_build_command=['pnpm', 'build:production'])
        self.write_package_json()

        self.run_command()

        build_call = self.mock_run.call_args_list[0]
        expected_call = call(['/usr/bin/pnpm', 'build:production'], cwd=self.app_folder)
        self.assertEqual(build_call, expected_call)

    def test_ww_test__skips_the_build_and_says_so__when_test_build_command_is_none(self):
        self.config = WebsiteWidgetsConfig(test_build_command=None)
        self.write_package_json()
        self.return_codes([0, 0])

        exit_code, output, _ = self.run_command()

        self.assertEqual(self.mock_run.call_count, 2)
        self.assertEqual(exit_code, 0)
        self.assertIn('Build: skipped (test_build_command is None)', output)

    def test_ww_test__skips_the_build_and_passes_the_rest_to_test__when_no_build_given(self):
        self.write_package_json()
        self.return_codes([0, 0])

        exit_code, output, _ = self.run_command('--no-build', '--exclude-tag=playwright')

        first_call = self.mock_run.call_args_list[0]
        expected_call = call([sys.executable, 'manage.py', 'test', '--exclude-tag=playwright'])
        self.assertEqual(first_call, expected_call)
        self.assertEqual(exit_code, 0)
        self.assertIn('Build: skipped (--no-build)', output)

    def test_ww_test__runs_no_tests_and_fails__when_the_build_fails(self):
        self.write_package_json()
        self.return_codes([1])

        exit_code, output, _ = self.run_command()

        expected_summary = (
            'Build: failed\n'
            'Python tests: skipped (the build failed)\n'
            'npm tests: skipped (the build failed)'
        )
        self.assertEqual(self.mock_run.call_count, 1)
        self.assertEqual(exit_code, 1)
        self.assertIn(expected_summary, output)

    def test_ww_test__says_to_run_npm_install_first__when_node_modules_is_missing(self):
        self.write_package_json(node_modules=False)

        exit_code, output, _ = self.run_command()

        shown_folder = os.path.relpath(self.app_folder) + os.sep
        self.mock_run.assert_not_called()
        self.assertEqual(exit_code, 1)
        self.assertIn(f'Build: failed (no node_modules/: run `npm install` in {shown_folder} first)', output)

    def test_ww_test__says_to_run_npm_install_first__when_node_modules_is_missing_and_build_is_off(self):
        self.config = WebsiteWidgetsConfig(test_build_command=None)
        self.write_package_json(node_modules=False)
        self.return_codes([0])

        exit_code, output, _ = self.run_command()

        self.assertEqual(self.mock_run.call_count, 1)
        self.assertEqual(exit_code, 1)
        self.assertIn('npm tests: failed (no node_modules/: run `npm install`', output)

    def test_ww_test__names_the_setting__when_package_json_has_no_build_script(self):
        self.write_package_json(scripts={'test': 'vitest run'})

        exit_code, output, _ = self.run_command()

        self.mock_run.assert_not_called()
        self.assertEqual(exit_code, 1)
        self.assertIn('package.json has no `build` script: add one, or set WEBSITE_WIDGETS.test_build_command', output)

    def test_ww_test__fails__when_the_build_command_is_not_found(self):
        self.write_package_json()
        self.mock_which.side_effect = lambda name: None

        exit_code, output, _ = self.run_command()

        self.mock_run.assert_not_called()
        self.assertEqual(exit_code, 1)
        self.assertIn('Build: failed (npm was not found', output)

    def test_ww_test__runs_both_and_fails__when_the_python_tests_fail(self):
        self.write_package_json()
        self.return_codes([0, 1, 0])

        exit_code, output, _ = self.run_command()

        expected_summary = (
            'Python tests: failed\n'
            'npm tests: passed'
        )
        self.assertEqual(self.mock_run.call_count, 3)
        self.assertEqual(exit_code, 1)
        self.assertIn(expected_summary, output)

    def test_ww_test__fails__when_the_npm_tests_fail(self):
        self.write_package_json()
        self.return_codes([0, 0, 1])

        exit_code, output, _ = self.run_command()

        self.assertEqual(exit_code, 1)
        self.assertIn('npm tests: failed', output)

    def test_ww_test__runs_python_alone_and_says_so__when_there_is_no_package_json(self):
        self.return_codes([0])

        exit_code, output, _ = self.run_command()

        expected_calls = [
            call([sys.executable, 'manage.py', 'test']),
        ]
        self.assertEqual(self.mock_run.call_args_list, expected_calls)
        self.assertEqual(exit_code, 0)
        self.assertIn('Build: skipped (no package.json', output)
        self.assertIn('npm tests: skipped (no package.json', output)

    def test_ww_test__runs_python_alone_and_says_so__when_package_json_has_no_test_script(self):
        self.write_package_json(scripts={'build': 'webpack'})
        self.return_codes([0, 0])

        exit_code, output, _ = self.run_command()

        self.assertEqual(self.mock_run.call_count, 2)
        self.assertEqual(exit_code, 0)
        self.assertIn('has no test script', output)

    def test_ww_test__fails__when_there_is_a_test_script_but_no_npm_for_it(self):
        self.config = WebsiteWidgetsConfig(test_build_command=None)
        self.write_package_json()
        self.mock_which.side_effect = lambda name: None
        self.return_codes([0])

        exit_code, output, _ = self.run_command()

        self.assertEqual(exit_code, 1)
        self.assertIn('npm tests: failed (npm was not found', output)

    def test_ww_test__prints_its_own_help__when_asked(self):
        exit_code, output, _ = self.run_command('--help')

        self.mock_run.assert_not_called()
        self.assertEqual(exit_code, 0)
        self.assertIn('npm test', output)
