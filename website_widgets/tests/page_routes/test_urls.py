from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.urls import path

from website_widgets import PageRoutes, register_url
from website_widgets.config import WebsiteWidgetsConfig
from website_widgets.web_page import AsyncWebPage
from website_widgets.tests.page_routes.page_routes_test_case import PageRoutesTestCase


class UrlsTestCase(PageRoutesTestCase):
    def test_urls__namespaces_routes_by_website_app_name__when_included(self):
        config = WebsiteWidgetsConfig(website_app_name='storefront')
        self.enterContext(patch('website_widgets.page_routes.get_config', return_value=config))

        page_urls = PageRoutes.urls()

        self.assertEqual(page_urls.app_name, 'storefront')
        self.assertEqual(page_urls.namespace, 'storefront')

    def test_urls__fails_naming_the_label_and_installed_apps__when_website_app_is_not_installed(self):
        self.mock_apps.get_app_config.side_effect = LookupError

        with self.assertRaisesMessage(ImproperlyConfigured, "Add 'website' to INSTALLED_APPS"):
            PageRoutes.urls()

    def test_urls__is_accepted_by_path__when_included(self):
        @register_url('forum/<int:post_id>', name='forum_post')
        class ForumPostPage(AsyncWebPage):
            pass

        page_urls = PageRoutes.urls()

        url_resolver = path('', page_urls)

        routes = [
            str(url_pattern.pattern)
            for url_pattern in url_resolver.url_patterns
        ]
        self.assertEqual(url_resolver.app_name, 'website')
        self.assertEqual(url_resolver.namespace, 'website')
        self.assertEqual(routes, ['forum/<int:post_id>'])

    def test_urls__routes_page__when_only_discovery_imports_its_module(self):
        self.write_page_module('nested_page/__init__.py', '')
        self.write_page_module(
            'nested_page/nested_page.py',
            'from website_widgets import AsyncWebPage, register_url\n'
            '\n'
            '\n'
            "@register_url('nested', name='nested')\n"
            'class NestedPage(AsyncWebPage):\n'
            '    pass\n')

        routes = self.get_routes_in_url_order()

        self.assertEqual(routes, ['nested'])

    def test_urls__orders_fixed_segment_first__when_parameter_could_match_it(self):
        @register_url('profile/<str:username>', name='profile')
        class ProfilePage(AsyncWebPage):
            pass

        @register_url('profile/settings', name='profile_settings')
        class SettingsPage(AsyncWebPage):
            pass

        routes = self.get_routes_in_url_order()

        self.assertEqual(routes, ['profile/settings', 'profile/<str:username>'])

    def test_urls__orders_longer_route_first__when_path_parameter_could_match_it(self):
        @register_url('files/<path:file_path>', name='file')
        class FilePage(AsyncWebPage):
            pass

        @register_url('files/<path:file_path>/history', name='file_history')
        class FileHistoryPage(AsyncWebPage):
            pass

        routes = self.get_routes_in_url_order()

        self.assertEqual(routes, ['files/<path:file_path>/history', 'files/<path:file_path>'])

    def test_urls__orders_alphabetically__when_routes_are_equally_specific(self):
        @register_url('tabs/<int:tab_id>', name='tab')
        class TabPage(AsyncWebPage):
            pass

        @register_url('forum/<int:post_id>', name='forum_post')
        class ForumPostPage(AsyncWebPage):
            pass

        routes = self.get_routes_in_url_order()

        self.assertEqual(routes, ['forum/<int:post_id>', 'tabs/<int:tab_id>'])
