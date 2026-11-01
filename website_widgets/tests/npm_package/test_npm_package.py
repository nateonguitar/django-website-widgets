import json
import os
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from website_widgets.management.npm_package import NpmPackage, NpmVersion


class NpmPackageTestCase(SimpleTestCase):
    """`RANGE` is patched to `^1.2.0-rc.1`, so the tests don't move when the real range is raised."""

    def setUp(self):
        self.enterContext(patch.object(NpmPackage, 'RANGE', '^1.2.0-rc.1'))
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.app_folder = temp_dir.name
        mock_apps = self.enterContext(patch('website_widgets.management.npm_package.apps'))
        mock_apps.get_app_config.return_value = SimpleNamespace(path=self.app_folder)
        self.mock_apps = mock_apps

    def install(self, version: str):
        folder = os.path.join(self.app_folder, 'node_modules', NpmPackage.NAME)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, 'package.json'), 'w', encoding='utf-8') as file:
            json.dump({'name': NpmPackage.NAME, 'version': version}, file)

    def test_range_allows__accepts__when_version_is_the_range_or_a_later_release_of_its_major(self):
        for version in ('1.2.0-rc.1', '1.2.0-rc.2', '1.2.0', '1.2.5', '1.9.0'):
            with self.subTest(version=version):
                self.assertTrue(NpmPackage.range_allows(NpmVersion.parse(version)))

    def test_range_allows__rejects__when_version_is_lower_another_major_or_another_releases_prerelease(self):
        for version in ('1.1.9', '1.2.0-beta.1', '2.0.0', '1.3.0-rc.1'):
            with self.subTest(version=version):
                self.assertFalse(NpmPackage.range_allows(NpmVersion.parse(version)))

    def test_is_registry_spec__tells_a_range_from_a_folder_or_git__when_given_either(self):
        for spec in ('^1.2.0', '1.2.0', '>=1.2.0', 'latest'):
            with self.subTest(spec=spec):
                self.assertTrue(NpmPackage.is_registry_spec(spec))
        for spec in ('file:../../../frontend', 'github:nateonguitar/django-website-widgets', '../frontend'):
            with self.subTest(spec=spec):
                self.assertFalse(NpmPackage.is_registry_spec(spec))

    def test_check_installed_version__warns_with_the_install_command__when_installed_version_is_outside_the_range(self):
        self.install('1.1.0')

        warnings = NpmPackage.check_installed_version()

        self.assertEqual([warning.id for warning in warnings], ['website_widgets.W002'])
        self.assertIn('1.1.0', warnings[0].msg)
        self.assertIn('^1.2.0-rc.1', warnings[0].msg)
        self.assertIn(NpmPackage.install_command(), warnings[0].hint)

    def test_check_installed_version__passes__when_installed_version_is_in_the_range(self):
        self.install('1.2.3')

        self.assertEqual(NpmPackage.check_installed_version(), [])

    def test_check_installed_version__passes__when_nothing_is_installed(self):
        self.assertEqual(NpmPackage.check_installed_version(), [])

    def test_check_installed_version__passes__when_website_app_is_not_installed(self):
        self.mock_apps.get_app_config.side_effect = LookupError

        self.assertEqual(NpmPackage.check_installed_version(), [])
