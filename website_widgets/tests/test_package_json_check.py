import json
import os
import tempfile

from django.test import SimpleTestCase

from website_widgets.management.package_json_check import PackageJsonCheck
from website_widgets.management.starter_site import StarterSite


class PackageJsonCheckTestCase(SimpleTestCase):
    """Each test writes the app's package.json into a temp folder and checks it."""

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.app_folder = temp_dir.name
        self.starter = json.loads(StarterSite('website').file('package.json'))

    def run_check(self, content: str):
        with open(os.path.join(self.app_folder, 'package.json'), 'w', encoding='utf-8') as file:
            file.write(content)
        package_json_check = PackageJsonCheck(
            app_folder=self.app_folder,
            app_label='website')
        return package_json_check.run()

    def test_run__finds_nothing_to_fix__when_file_is_the_starters(self):
        fixes = self.run_check(json.dumps(self.starter))

        self.assertTrue(fixes.is_empty())

    def test_run__accepts_a_build_tool__when_it_is_under_dependencies_instead(self):
        webpack_range = self.starter['devDependencies'].pop('webpack')
        self.starter['dependencies'] = {'webpack': webpack_range}

        fixes = self.run_check(json.dumps(self.starter))

        self.assertTrue(fixes.is_empty())

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

        self.assertIsNone(fixes.error)
        self.assertEqual(
            fixes.packages_to_install,
            [f'{name}@{version_range}' for name, version_range in self.starter['devDependencies'].items()])
        self.assertEqual(list(fixes.missing_scripts), ['build', 'watch'])

    def test_run__accepts_a_version__when_it_is_not_a_string(self):
        self.starter['devDependencies']['webpack'] = 5

        fixes = self.run_check(json.dumps(self.starter))

        self.assertTrue(fixes.is_empty())


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
                self.assertEqual(PackageJsonCheck.minimum_version(version_range), expected)

    def test_minimum_version__returns_none__when_range_names_no_version(self):
        for version_range in ('latest', '*', 'github:user/repo', 'file:../lib', 5, None):
            with self.subTest(version_range=version_range):
                self.assertIsNone(PackageJsonCheck.minimum_version(version_range))
