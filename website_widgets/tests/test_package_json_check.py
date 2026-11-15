import copy
import json
import os
import tempfile

from django.test import SimpleTestCase

from website_widgets.management.npm_package import NpmPackage
from website_widgets.management.package_json_check import PackageJsonCheck
from website_widgets.management.starter_site import StarterSite


class PackageJsonCheckTestCase(SimpleTestCase):
    """Each test writes the app's package.json into a temp folder and checks it."""

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.app_folder = temp_dir.name
        starter_site = StarterSite('website')
        starter_package_json = starter_site.file('package.json')
        self.starter = json.loads(starter_package_json)

    def run_check(self, content: str):
        package_json_path = os.path.join(self.app_folder, 'package.json')
        with open(package_json_path, 'w', encoding='utf-8') as file:
            file.write(content)
        package_json_check = PackageJsonCheck(
            app_folder=self.app_folder,
            app_label='website')
        return package_json_check.run()

    def test_run__finds_nothing_to_fix__when_file_is_the_starters(self):
        content = json.dumps(self.starter)

        fixes = self.run_check(content)

        nothing_to_fix = fixes.is_empty()
        self.assertTrue(nothing_to_fix)

    def test_run__accepts_a_build_tool__when_it_is_under_dependencies_instead(self):
        webpack_range = self.starter['devDependencies'].pop('webpack')
        self.starter['dependencies']['webpack'] = webpack_range
        content = json.dumps(self.starter)

        fixes = self.run_check(content)

        nothing_to_fix = fixes.is_empty()
        self.assertTrue(nothing_to_fix)

    def test_run__says_to_install_the_npm_package__when_it_is_missing_or_below_the_range(self):
        install_command = NpmPackage.install_command()
        for spec in (None, '^0.9.0'):
            with self.subTest(spec=spec):
                starter = copy.deepcopy(self.starter)
                if spec is None:
                    del starter['dependencies'][NpmPackage.NAME]
                else:
                    starter['dependencies'][NpmPackage.NAME] = spec
                content = json.dumps(starter)

                fixes = self.run_check(content)

                fix_lines = fixes.fix_lines('website')
                self.assertEqual(fix_lines, [f'In website/, run: {install_command}'])

    def test_run__accepts_the_npm_package__when_it_is_a_local_folder(self):
        self.starter['dependencies'][NpmPackage.NAME] = 'file:../../../frontend'
        content = json.dumps(self.starter)

        fixes = self.run_check(content)

        nothing_to_fix = fixes.is_empty()
        self.assertTrue(nothing_to_fix)

    def test_run__reports_an_error__when_file_is_not_a_json_object(self):
        for content in ('[]', '"website"', 'null'):
            with self.subTest(content=content):
                fixes = self.run_check(content)

                self.assertEqual(fixes.error, 'package.json holds no JSON object.')

    def test_run__reports_an_error__when_file_is_not_valid_json(self):
        fixes = self.run_check('{ "name": ')

        self.assertIn('package.json is not valid JSON', fixes.error)

    def test_run__reports_every_tool_and_script__when_their_sections_are_not_objects(self):
        fixes = self.run_check('{"devDependencies": null, "dependencies": [], "scripts": "webpack"}')

        expected_packages = [
            f'{name}@{version_range}'
            for name, version_range in self.starter['devDependencies'].items()
        ]
        missing_scripts = list(fixes.missing_scripts)
        self.assertIsNone(fixes.error)
        self.assertEqual(fixes.packages_to_install, expected_packages)
        self.assertEqual(missing_scripts, ['build', 'watch'])

    def test_run__accepts_a_version__when_it_is_not_a_string(self):
        self.starter['devDependencies']['webpack'] = 5
        content = json.dumps(self.starter)

        fixes = self.run_check(content)

        nothing_to_fix = fixes.is_empty()
        self.assertTrue(nothing_to_fix)


class MinimumVersionTestCase(SimpleTestCase):
    def test_minimum_version__reads_the_lowest_version_allowed__when_range_is_one_npm_writes(self):
        cases = {
            '^5.110.2': (5, 110, 2),
            '~9.5': (9, 5, 0),
            '>=7': (7, 0, 0),
            '16.0.4': (16, 0, 4),
            'v1.2.3': (1, 2, 3),
        }
        for version_range, expected in cases.items():
            with self.subTest(version_range=version_range):
                minimum = PackageJsonCheck.minimum_version(version_range)

                self.assertEqual(minimum, expected)

    def test_minimum_version__returns_none__when_range_names_no_version(self):
        for version_range in ('latest', '*', 'github:user/repo', 'file:../lib', 5, None):
            with self.subTest(version_range=version_range):
                minimum = PackageJsonCheck.minimum_version(version_range)

                self.assertIsNone(minimum)
