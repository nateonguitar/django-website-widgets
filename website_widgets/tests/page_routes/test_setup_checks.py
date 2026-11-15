import os
import tempfile

from django.test import override_settings
from django.urls import path

from website_widgets import PageRoutes, register_url
from website_widgets.web_page import AsyncWebPage
from website_widgets.tests.page_routes.page_routes_test_case import PageRoutesTestCase


class CheckWebsiteAppIsInstalledTestCase(PageRoutesTestCase):
    def setUp(self):
        super().setUp()
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.base_dir = temp_dir.name
        self.enterContext(override_settings(BASE_DIR=self.base_dir))

    def write_app_folder(self):
        app_folder = os.path.join(self.base_dir, 'website')
        os.makedirs(app_folder)
        apps_py_path = os.path.join(app_folder, 'apps.py')
        with open(apps_py_path, 'w', encoding='utf-8') as file:
            file.write('')

    def uninstall_website_app(self):
        self.mock_apps.get_app_config.side_effect = LookupError

    def test_check_website_app_is_installed__fails__when_app_folder_exists_but_app_is_not_installed(self):
        self.write_app_folder()
        self.uninstall_website_app()

        errors = PageRoutes.check_website_app_is_installed()

        error_ids = [
            error.id
            for error in errors
        ]
        self.assertEqual(error_ids, ['website_widgets.E002'])
        self.assertIn("Add 'website' to INSTALLED_APPS", errors[0].hint)

    def test_check_website_app_is_installed__passes__when_there_is_no_app_folder(self):
        self.uninstall_website_app()

        errors = PageRoutes.check_website_app_is_installed()

        self.assertEqual(errors, [])

    def test_check_website_app_is_installed__passes__when_app_is_installed(self):
        self.write_app_folder()

        errors = PageRoutes.check_website_app_is_installed()

        self.assertEqual(errors, [])


class CheckPagesAreRoutedTestCase(PageRoutesTestCase):
    def test_check_pages_are_routed__fails__when_no_url_pattern_includes_the_pages(self):
        @register_url('about', name='about')
        class AboutPage(AsyncWebPage):
            pass

        self.use_urlconf([])

        errors = PageRoutes.check_pages_are_routed()

        error_ids = [
            error.id
            for error in errors
        ]
        self.assertEqual(error_ids, ['website_widgets.E003'])
        self.assertIn("include('website.urls')", errors[0].hint)

    def test_check_pages_are_routed__passes__when_urls_include_the_pages(self):
        @register_url('about', name='about')
        class AboutPage(AsyncWebPage):
            pass

        page_urls = PageRoutes.urls()
        page_routes_include = path('', page_urls)
        self.use_urlconf([page_routes_include])

        errors = PageRoutes.check_pages_are_routed()

        self.assertEqual(errors, [])

    def test_check_pages_are_routed__passes__when_there_are_no_pages(self):
        self.use_urlconf([])

        errors = PageRoutes.check_pages_are_routed()

        self.assertEqual(errors, [])
