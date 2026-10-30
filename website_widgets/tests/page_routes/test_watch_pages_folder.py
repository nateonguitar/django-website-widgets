import shutil
from pathlib import Path
from unittest.mock import MagicMock

from django.utils.autoreload import StatReloader, autoreload_started

from website_widgets import PageRoutes
from website_widgets.tests.page_routes.page_routes_test_case import PageRoutesTestCase


class WatchPagesFolderTestCase(PageRoutesTestCase):
    def test_watch_pages_folder__watches_every_python_file_under_pages__when_runserver_starts(self):
        reloader = MagicMock()

        PageRoutes.watch_pages_folder(sender=reloader)

        reloader.watch_dir.assert_called_once_with(Path(self.pages_folder), '**/*.py')

    def test_watch_pages_folder__watches_nothing__when_website_app_is_not_installed(self):
        self.mock_apps.get_app_config.side_effect = LookupError
        reloader = MagicMock()

        PageRoutes.watch_pages_folder(sender=reloader)

        reloader.watch_dir.assert_not_called()

    def test_watch_pages_folder__watches_nothing__when_app_has_no_pages_folder(self):
        shutil.rmtree(self.pages_folder)
        reloader = MagicMock()

        PageRoutes.watch_pages_folder(sender=reloader)

        reloader.watch_dir.assert_not_called()

    def test_watch_pages_folder__is_connected__when_the_app_is_ready(self):
        # A real reloader, through Django's own signal: what runserver's autoreloader sends.
        reloader = StatReloader()

        autoreload_started.send(sender=reloader)

        self.assertIn('**/*.py', reloader.directory_globs[Path(self.pages_folder).absolute()])
