import os
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from website_widgets.management.test_runner_check import TestRunnerCheck


class TestRunnerCheckTestCase(SimpleTestCase):
    """The website app is a temp folder with a package.json unless a test removes it."""

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.app_folder = temp_dir.name
        self.package_json_path = os.path.join(self.app_folder, 'package.json')
        with open(self.package_json_path, 'w') as package_json_file:
            package_json_file.write('{}')
        self.mock_apps = self.enterContext(patch('website_widgets.management.test_runner_check.apps'))
        self.mock_apps.get_app_config.return_value = SimpleNamespace(path=self.app_folder)

    @override_settings(TEST_RUNNER='django.test.runner.DiscoverRunner')
    def test_check_test_runner__warns_naming_the_runner_and_the_silencing__when_it_is_djangos(self):
        messages = TestRunnerCheck.check_test_runner()

        warning = messages[0]
        self.assertEqual(len(messages), 1)
        self.assertEqual(warning.id, 'website_widgets.W003')
        self.assertIn("TEST_RUNNER is 'django.test.runner.DiscoverRunner'", warning.msg)
        self.assertIn("TEST_RUNNER = 'website_widgets.testing.WebsiteWidgetsTestRunner'", warning.hint)
        self.assertIn('SILENCED_SYSTEM_CHECKS', warning.hint)

    @override_settings(TEST_RUNNER='website_widgets.testing.WebsiteWidgetsTestRunner')
    def test_check_test_runner__passes__when_it_is_the_packages_runner(self):
        messages = TestRunnerCheck.check_test_runner()

        self.assertEqual(messages, [])

    @override_settings(TEST_RUNNER='website_widgets.tests.testing.sample_suites.SwitchingRunner')
    def test_check_test_runner__passes__when_it_is_a_subclass(self):
        messages = TestRunnerCheck.check_test_runner()

        self.assertEqual(messages, [])

    @override_settings(TEST_RUNNER='django.test.runner.DiscoverRunner')
    def test_check_test_runner__passes__when_the_app_has_no_package_json(self):
        os.remove(self.package_json_path)

        messages = TestRunnerCheck.check_test_runner()

        self.assertEqual(messages, [])

    @override_settings(TEST_RUNNER='django.test.runner.DiscoverRunner')
    def test_check_test_runner__passes__when_the_website_app_is_not_installed(self):
        self.mock_apps.get_app_config.side_effect = LookupError('No installed app with label')

        messages = TestRunnerCheck.check_test_runner()

        self.assertEqual(messages, [])

    @override_settings(TEST_RUNNER='mysite.no_such_module.Runner')
    def test_check_test_runner__passes__when_the_runner_cannot_be_imported(self):
        messages = TestRunnerCheck.check_test_runner()

        self.assertEqual(messages, [])
