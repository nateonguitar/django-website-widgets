import io
import json
import os
import subprocess
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from django.core import checks
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.test import SimpleTestCase

from website_widgets.management.npm_package import NpmPackage
from website_widgets.management.starter_site import StarterSite


COMMAND_MODULE = 'website_widgets.management.commands.ww_doctor'


class WwDoctorTestCase(SimpleTestCase):
    """
    A temp website app holding the starter's package.json, every build tool and the npm package in
    node_modules and a built bundle, with node 22 and npm 10 on the PATH, so each test breaks one
    thing.
    """

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.app_folder = os.path.join(temp_dir.name, 'website')
        os.makedirs(self.app_folder)
        self.starter_site = StarterSite('website')
        self.write(self.starter_site.file('package.json'), 'package.json')
        for name in ('css-loader', 'mini-css-extract-plugin', 'sass', 'sass-loader', 'ts-loader', 'typescript', 'webpack', 'webpack-cli'):
            os.makedirs(os.path.join(self.app_folder, 'node_modules', name))
        self.install_npm_package(NpmPackage.range_minimum().as_text())

        self.mock_apps = self.enterContext(patch(f'{COMMAND_MODULE}.apps'))
        self.mock_apps.get_app_config.return_value = SimpleNamespace(path=self.app_folder)
        self.check_messages = []
        self.enterContext(patch(f'{COMMAND_MODULE}.checks.run_checks', side_effect=lambda: self.check_messages))
        self.versions = {'node': 'v22.3.0', 'npm': '10.8.1'}
        self.enterContext(patch(f'{COMMAND_MODULE}.shutil.which', side_effect=self.which))
        self.enterContext(patch(f'{COMMAND_MODULE}.subprocess.run', side_effect=self.run_version))
        self.built_files = {'main.js', 'bundled-styles.css'}
        self.enterContext(patch(
            f'{COMMAND_MODULE}.finders.find',
            side_effect=lambda filename: f'/static/{filename}' if filename in self.built_files else None))

    def which(self, command: str) -> str | None:
        return f'/usr/bin/{command}' if command in self.versions else None

    def run_version(self, args: list[str], **kwargs) -> subprocess.CompletedProcess:
        command = os.path.basename(args[0])
        return subprocess.CompletedProcess(args, 0, stdout=f'{self.versions[command]}\n')

    def write(self, content: str, *path_parts: str):
        with open(os.path.join(self.app_folder, *path_parts), 'w', encoding='utf-8') as file:
            file.write(content)

    def install_npm_package(self, version: str):
        folder = os.path.join(self.app_folder, 'node_modules', NpmPackage.NAME)
        os.makedirs(folder, exist_ok=True)
        self.write(json.dumps({'name': NpmPackage.NAME, 'version': version}), 'node_modules', NpmPackage.NAME, 'package.json')

    def run_doctor(self) -> str:
        """The checklist printed; the exit status is kept as `self.exit_code`."""
        output = io.StringIO()
        self.exit_code = 0
        try:
            call_command('ww_doctor', stdout=output)
        except SystemExit as system_exit:
            self.exit_code = system_exit.code
        return output.getvalue()

    def test_doctor__reports_no_problems_and_exits_zero__when_everything_is_set_up(self):
        output = self.run_doctor()

        self.assertNotIn('[✗]', output)
        self.assertIn('[✓] node v22.3.0', output)
        self.assertIn('[✓] npm 10.8.1', output)
        self.assertIn('No problems found.', output)
        self.assertEqual(self.exit_code, 0)

    def test_doctor__exits_with_status_1_after_the_checklist__when_there_is_a_problem(self):
        self.versions.pop('npm')

        output = self.run_doctor()

        self.assertEqual(self.exit_code, 1)
        self.assertTrue(output.endswith('1 problem found.\n'))

    def test_doctor__reports_the_error_and_goes_on__when_a_system_check_raises(self):
        self.mock_apps.get_app_config.side_effect = LookupError
        self.enterContext(patch(
            f'{COMMAND_MODULE}.checks.run_checks',
            side_effect=ImproperlyConfigured("Add 'website' to INSTALLED_APPS.")))

        output = self.run_doctor()

        self.assertIn(
            "[✗] The system checks stopped on an error: ImproperlyConfigured: Add 'website' to INSTALLED_APPS.",
            output)
        self.assertIn("[✗] No installed app is labelled 'website'", output)
        self.assertIn('[✓] node v22.3.0', output)
        self.assertIn('2 problems found.', output)
        self.assertEqual(self.exit_code, 1)

    def test_doctor__says_the_app_is_not_installed_once__when_e002_already_says_so(self):
        self.mock_apps.get_app_config.side_effect = LookupError
        self.check_messages = [
            checks.Error("'website' isn't in INSTALLED_APPS.", hint="Add 'website'.", id='website_widgets.E002'),
        ]

        output = self.run_doctor()

        self.assertIn("[✗] website_widgets.E002: 'website' isn't in INSTALLED_APPS.", output)
        self.assertNotIn('No installed app is labelled', output)
        self.assertIn('1 problem found.', output)

    def test_doctor__lists_each_failing_system_check_with_its_hint__when_one_fails(self):
        self.check_messages = [
            checks.Error('Not routed.', hint='Include the pages.', id='website_widgets.E003'),
            checks.Error('Not ours.', id='admin.E001'),
        ]

        output = self.run_doctor()

        self.assertIn('[✗] website_widgets.E003: Not routed.', output)
        self.assertIn('    Include the pages.', output)
        self.assertNotIn('admin.E001', output)

    def test_doctor__says_how_to_install_node__when_node_is_missing(self):
        del self.versions['node']

        output = self.run_doctor()

        self.assertIn('[✗] node is not on the PATH', output)
        self.assertIn('https://nodejs.org', output)

    def test_doctor__fails_node__when_it_is_older_than_the_build_tools_need(self):
        self.versions['node'] = 'v16.20.0'

        output = self.run_doctor()

        self.assertIn('[✗] node is v16.20.0, older than the build tools need (18.12.0)', output)

    def test_doctor__fails_naming_the_package_managers__when_none_is_installed(self):
        del self.versions['npm']

        output = self.run_doctor()

        self.assertIn('[✗] No JavaScript package manager is installed (npm, yarn, pnpm)', output)
        self.assertIn('https://nodejs.org', output)
        self.assertIn('node_and_package_managers.md', output)

    def test_doctor__passes_saying_the_watcher_is_the_projects__when_yarn_is_installed_without_npm(self):
        del self.versions['npm']
        self.versions['yarn'] = '1.22.22'

        output = self.run_doctor()

        self.assertIn('[✓] yarn 1.22.22, with no npm: start_npm_watch() runs npm', output)

    def test_doctor__prints_install_command__when_package_json_declares_a_tool_too_low(self):
        self.write(self.starter_site.file('package.json').replace('"^5.110.2"', '"^5.97.1"'), 'package.json')

        output = self.run_doctor()

        self.assertIn("package.json lacks what the starter site's build needs", output)
        self.assertIn('npm install --save-dev webpack@^5.110.2', output)

    def test_doctor__says_to_run_npm_install__when_node_modules_lacks_a_tool(self):
        os.rmdir(os.path.join(self.app_folder, 'node_modules', 'ts-loader'))

        output = self.run_doctor()

        self.assertIn('node_modules/ lacks ts-loader', output)
        self.assertIn('run: npm install', output)

    def test_doctor__says_to_install_the_npm_package__when_installed_version_is_outside_the_range(self):
        self.install_npm_package('0.9.0')

        output = self.run_doctor()

        self.assertIn(f'is 0.9.0, outside {NpmPackage.RANGE}', output)
        self.assertIn(NpmPackage.install_command(), output)
        self.assertEqual(self.exit_code, 1)

    def test_doctor__says_to_build__when_bundle_is_not_built(self):
        self.built_files = {'bundled-styles.css'}

        output = self.run_doctor()

        self.assertIn('[✗] No built main.js in the static files', output)
        self.assertIn('npm run build', output)

    def test_doctor__skips_app_folder_checks__when_website_app_is_not_installed(self):
        self.mock_apps.get_app_config.side_effect = LookupError

        output = self.run_doctor()

        self.assertIn("[✗] No installed app is labelled 'website'", output)
        self.assertNotIn('package.json', output)
        self.assertIn('1 problem found.', output)
