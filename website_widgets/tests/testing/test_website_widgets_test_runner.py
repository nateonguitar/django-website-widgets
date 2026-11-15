import json
import logging
import os
import tempfile
from argparse import ArgumentParser
from types import SimpleNamespace
from unittest.mock import call, patch

from django.core.management.base import CommandError
from django.test import SimpleTestCase
from django.test.runner import ParallelTestSuite

from website_widgets.config import TestingConfig, WebsiteWidgetsConfig
from website_widgets.testing import WebsiteWidgetsParallelTestSuite, WebsiteWidgetsTestRunner
# Through the module, never imported by name: a test case class in this module's namespace would
# be discovered and run as one of its tests.
from website_widgets.tests.testing import sample_suites
from website_widgets.tests.testing.sample_suites import SwitchedOff, SwitchingRunner


class WebsiteWidgetsTestRunnerTestCase(SimpleTestCase):
    """
    Nothing is built: `subprocess.run` and `shutil.which` are mocked, the website app is a temp
    folder, and each test sets the config's testing settings.
    """

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.app_folder = temp_dir.name
        self.mock_apps = self.enterContext(patch('website_widgets.management.website_app.apps'))
        self.mock_apps.get_app_config.return_value = SimpleNamespace(path=self.app_folder)
        self.config = WebsiteWidgetsConfig()
        get_config = lambda: self.config
        self.enterContext(patch('website_widgets.management.website_app.get_config', side_effect=get_config))
        self.enterContext(patch('website_widgets.testing.get_config', side_effect=get_config))
        self.mock_run = self.enterContext(patch('website_widgets.testing.subprocess.run'))
        self.mock_run.return_value = SimpleNamespace(returncode=0)
        # The one `shutil.which`, which the build checks and the runner both call.
        self.mock_which = self.enterContext(patch('shutil.which'))
        self.mock_which.side_effect = lambda name: f'/usr/bin/{name}'

    def write_package_json(self, scripts: dict | None = None, node_modules: bool = True):
        """A package.json with these scripts (a build script unless given), and node_modules/ unless told not to."""
        if scripts is None:
            scripts = {'build': 'webpack'}
        package_json_path = os.path.join(self.app_folder, 'package.json')
        with open(package_json_path, 'w') as package_json_file:
            json.dump({'scripts': scripts}, package_json_file)
        if node_modules:
            node_modules_path = os.path.join(self.app_folder, 'node_modules')
            os.makedirs(node_modules_path)

    def build_suite(self, *test_case_names: str, runner_class=WebsiteWidgetsTestRunner, **runner_kwargs):
        """The runner's suite for these classes in `sample_suites`, built from their labels as `manage.py test` would."""
        runner = runner_class(verbosity=0, **runner_kwargs)
        test_labels = [f'{sample_suites.__name__}.{test_case_name}' for test_case_name in test_case_names]
        return runner.build_suite(test_labels)

    def test_build_suite__builds_the_frontend_in_the_app_folder__when_a_browser_test_is_selected(self):
        self.write_package_json()

        self.build_suite('ServerTests', 'BrowserTests')

        expected_calls = [
            call(['/usr/bin/npm', 'run', 'build'], cwd=self.app_folder),
        ]
        self.assertEqual(self.mock_run.call_args_list, expected_calls)

    def test_build_suite__builds_the_frontend__when_one_test_method_carries_the_tag(self):
        self.write_package_json()

        self.build_suite('OneBrowserTestTests')

        self.mock_run.assert_called_once()

    def test_build_suite__builds_nothing__when_no_browser_test_is_selected(self):
        self.write_package_json()

        self.build_suite('ServerTests')
        self.build_suite('BrowserTests', exclude_tags=['playwright'])

        self.mock_run.assert_not_called()

    def test_build_suite__builds_nothing__when_every_browser_test_is_skipped(self):
        self.write_package_json()

        self.build_suite('ServerTests', 'SkippedBrowserTests')

        self.mock_run.assert_not_called()

    def test_build_suite__builds_once__when_the_suite_is_split_among_parallel_workers(self):
        self.write_package_json()

        suite = self.build_suite('ServerTests', 'BrowserTests', parallel=2)

        self.assertIsInstance(suite, ParallelTestSuite)
        self.mock_run.assert_called_once()

    def test_build_suite__builds_for_the_configured_tag_alone__when_one_is_set(self):
        self.config = WebsiteWidgetsConfig(testing=TestingConfig(browser_test_tag='browser'))
        self.write_package_json()

        self.build_suite('BrowserTests', 'OneBrowserTestTests')
        calls_for_playwright_tests = self.mock_run.call_count
        self.build_suite('OtherTagBrowserTests')

        self.assertEqual(calls_for_playwright_tests, 0)
        self.mock_run.assert_called_once()

    def test_build_suite__runs_the_configured_command__when_set(self):
        testing = TestingConfig(build_command=['pnpm', 'build:production'])
        self.config = WebsiteWidgetsConfig(testing=testing)
        self.write_package_json()

        self.build_suite('BrowserTests')

        expected_call = call(['/usr/bin/pnpm', 'build:production'], cwd=self.app_folder)
        self.assertEqual(self.mock_run.call_args, expected_call)

    def test_build_suite__builds_nothing__when_no_build_is_given(self):
        self.write_package_json()

        self.build_suite('BrowserTests', no_build=True)

        self.mock_run.assert_not_called()

    def test_build_suite__builds_nothing__when_the_build_command_is_none(self):
        self.config = WebsiteWidgetsConfig(testing=TestingConfig(build_command=None))
        self.write_package_json()

        self.build_suite('BrowserTests')

        self.mock_run.assert_not_called()

    def test_build_suite__builds_nothing__when_the_app_has_no_package_json(self):
        self.build_suite('BrowserTests')

        self.mock_run.assert_not_called()

    def test_build_suite__fails_naming_the_command__when_the_build_fails(self):
        self.write_package_json()
        self.mock_run.return_value = SimpleNamespace(returncode=1)

        with self.assertRaises(CommandError) as caught:
            self.build_suite('BrowserTests')

        message = str(caught.exception)
        self.assertIn('The frontend build, npm run build, failed, so no test ran', message)
        self.assertIn('--no-build', message)

    def test_build_suite__says_to_run_npm_install_first__when_node_modules_is_missing(self):
        self.write_package_json(node_modules=False)

        with self.assertRaises(CommandError) as caught:
            self.build_suite('BrowserTests')

        shown_folder = os.path.relpath(self.app_folder) + os.sep
        message = str(caught.exception)
        self.mock_run.assert_not_called()
        self.assertIn(f'there is no node_modules/: run `npm install` in {shown_folder} first', message)

    def test_build_suite__names_the_setting__when_package_json_has_no_build_script(self):
        self.write_package_json(scripts={'test': 'vitest run'})

        with self.assertRaises(CommandError) as caught:
            self.build_suite('BrowserTests')

        message = str(caught.exception)
        self.mock_run.assert_not_called()
        self.assertIn('package.json has no `build` script: add one, or set WEBSITE_WIDGETS.testing.build_command', message)

    def test_build_suite__fails__when_the_build_command_is_not_found(self):
        self.write_package_json()
        self.mock_which.side_effect = lambda name: None

        with self.assertRaises(CommandError) as caught:
            self.build_suite('BrowserTests')

        message = str(caught.exception)
        self.mock_run.assert_not_called()
        self.assertIn('npm was not found', message)

    def test_build_suite__names_the_runner_for_the_workers__when_parallel(self):
        suite = self.build_suite('ServerTests', 'BrowserTests', runner_class=SwitchingRunner, parallel=2)

        expected_runner_path = f'{sample_suites.__name__}.SwitchingRunner'
        self.assertIsInstance(suite, WebsiteWidgetsParallelTestSuite)
        self.assertEqual(suite.process_setup_args, (expected_runner_path,))

    def test_build_suite__warns_naming_tblib__when_parallel_without_it(self):
        self.enterContext(patch('website_widgets.testing.tblib', None))
        logger = logging.getLogger('website_widgets.tests.runner')

        with self.assertLogs(logger, level=logging.WARNING) as logs:
            self.build_suite('ServerTests', 'BrowserTests', parallel=2, logger=logger)

        warning = logs.output[0]
        self.assertIn('tblib is not installed', warning)

    def test_process_setup__starts_the_runners_patches__when_a_worker_starts(self):
        self.addCleanup(SwitchingRunner.stop_patches)
        runner_path = f'{sample_suites.__name__}.SwitchingRunner'

        WebsiteWidgetsParallelTestSuite.process_setup(runner_path)

        self.assertFalse(SwitchedOff.is_on)

    def test_setup_test_environment__starts_the_patches_until_teardown__when_the_run_starts(self):
        runner = SwitchingRunner(verbosity=0)
        self.enterContext(patch('website_widgets.testing.DiscoverRunner.setup_test_environment'))
        self.enterContext(patch('website_widgets.testing.DiscoverRunner.teardown_test_environment'))

        runner.setup_test_environment()
        is_on_during_the_run = SwitchedOff.is_on
        runner.teardown_test_environment()

        self.assertFalse(is_on_during_the_run)
        self.assertTrue(SwitchedOff.is_on)

    def test_add_arguments__accepts_no_build__when_given_on_the_command_line(self):
        parser = ArgumentParser()
        WebsiteWidgetsTestRunner.add_arguments(parser)

        options = parser.parse_args(['--no-build'])

        self.assertTrue(options.no_build)
