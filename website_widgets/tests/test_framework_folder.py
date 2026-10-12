import importlib.metadata
import os
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from website_widgets.management.framework_folder import FrameworkFolder


class CheckVersionStampTestCase(SimpleTestCase):
    """A temp website app, its framework folder's README stamped with whichever version a test writes."""

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.app_folder = temp_dir.name
        self.mock_apps = self.enterContext(patch('website_widgets.management.framework_folder.apps'))
        self.mock_apps.get_app_config.return_value = SimpleNamespace(path=self.app_folder)
        self.installed = importlib.metadata.version('django-website-widgets')

    def write_readme(self, version: str):
        folder = os.path.join(self.app_folder, FrameworkFolder.RELATIVE_PATH)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, 'README.md'), 'w', encoding='utf-8') as file:
            file.write(f'# website_widgets frontend framework\n\nCopied from django-website-widgets {version} by `ww_upgrade`.\n')

    def test_check_version_stamp__warns_naming_both_versions__when_folder_is_from_another_version(self):
        self.write_readme('0.0.1')

        warnings = FrameworkFolder.check_version_stamp()

        self.assertEqual([warning.id for warning in warnings], ['website_widgets.W001'])
        self.assertIn('0.0.1', warnings[0].msg)
        self.assertIn(self.installed, warnings[0].msg)
        self.assertIn('ww_upgrade', warnings[0].hint)

    def test_check_version_stamp__passes__when_folder_matches_the_installed_version(self):
        self.write_readme(self.installed)

        self.assertEqual(FrameworkFolder.check_version_stamp(), [])

    def test_check_version_stamp__passes__when_there_is_no_framework_folder(self):
        self.assertEqual(FrameworkFolder.check_version_stamp(), [])

    def test_check_version_stamp__passes__when_website_app_is_not_installed(self):
        self.mock_apps.get_app_config.side_effect = LookupError

        self.assertEqual(FrameworkFolder.check_version_stamp(), [])
