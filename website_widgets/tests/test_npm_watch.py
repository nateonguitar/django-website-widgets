import io
import os
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from website_widgets import NpmWatch, start_npm_watch


class NpmWatchTestCase(SimpleTestCase):
    """No process is started: `Popen` and the process list are mocked, and the app is a temp folder."""

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.app_folder = temp_dir.name
        self.other_folder = os.path.join(temp_dir.name, 'other')
        os.makedirs(self.other_folder)

        mock_apps = self.enterContext(patch('django.apps.apps'))
        mock_apps.get_app_config.return_value = SimpleNamespace(path=self.app_folder)
        self.mock_popen = self.enterContext(patch('website_widgets.npm_watch.subprocess.Popen'))
        self.mock_process_iter = self.enterContext(patch('website_widgets.npm_watch.psutil.process_iter'))
        self.mock_process_iter.return_value = []
        self.enterContext(patch.dict(os.environ))
        os.environ.pop('RUN_MAIN', None)

    def running_process(self, cmdline: list[str] | None, cwd: str | None) -> SimpleNamespace:
        return SimpleNamespace(info={'cmdline': cmdline, 'cwd': cwd})

    def run_start(self, *argv: str):
        with patch.object(sys, 'argv', ['manage.py', *argv]):
            start_npm_watch()

    def test_start_npm_watch__starts_watch_in_app_folder__when_runserver_and_none_running(self):
        self.run_start('runserver')

        self.mock_popen.assert_called_once_with(['npm', 'run', 'watch'], cwd=self.app_folder)

    def test_start_npm_watch__starts_nothing__when_command_is_not_runserver(self):
        for argv in (('migrate',), ('test', 'runserver'), ()):
            with self.subTest(argv=argv):
                self.run_start(*argv)

        self.mock_popen.assert_not_called()

    def test_start_npm_watch__starts_nothing__when_in_autoreloader_child(self):
        os.environ['RUN_MAIN'] = 'true'

        self.run_start('runserver')

        self.mock_popen.assert_not_called()

    def test_start_npm_watch__starts_nothing__when_watch_already_running_in_app_folder(self):
        self.mock_process_iter.return_value = [
            self.running_process(['npm', 'run', 'watch'], self.app_folder),
        ]

        self.run_start('runserver')

        self.mock_popen.assert_not_called()

    def test_start_npm_watch__starts_watch__when_watch_running_only_in_another_folder(self):
        self.mock_process_iter.return_value = [
            self.running_process(['npm', 'run', 'watch'], self.other_folder),
            self.running_process(None, None),
            self.running_process(['npm', 'run', 'watch'], None),
        ]

        self.run_start('runserver')

        self.mock_popen.assert_called_once()

    def test_start_npm_watch__warns_and_returns__when_npm_is_not_installed(self):
        self.mock_popen.side_effect = FileNotFoundError
        stderr = self.enterContext(patch('website_widgets.npm_watch.sys.stderr', new_callable=io.StringIO))

        self.run_start('runserver')

        self.assertIn('npm was not found', stderr.getvalue())

    def test_start__is_start_npm_watch__when_imported(self):
        self.assertEqual(start_npm_watch, NpmWatch.start)
