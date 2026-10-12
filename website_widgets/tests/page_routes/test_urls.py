from unittest.mock import patch

from django.urls import path

from website_widgets import PageRoutes, register_url
from website_widgets.config import WebsiteWidgetsConfig
from website_widgets.web_page import WebPage
from website_widgets.tests.page_routes.page_routes_test_case import PageRoutesTestCase


class UrlsTestCase(PageRoutesTestCase):
    def test_urls__namespaces_routes_by_website_app_name__when_included(self):
        config = WebsiteWidgetsConfig(website_app_name='storefront')
        self.enterContext(patch('website_widgets.page_routes.get_config', return_value=config))

        urls = PageRoutes.urls()

        self.assertEqual((urls.app_name, urls.namespace), ('storefront', 'storefront'))

    def test_urls__is_accepted_by_path__when_included(self):
        @register_url('forum/<int:post_id>', name='forum_post')
        class ForumPostPage(WebPage):
            pass

        url_resolver = path('', PageRoutes.urls())

        self.assertEqual((url_resolver.app_name, url_resolver.namespace), ('website', 'website'))
        self.assertEqual([str(url_pattern.pattern) for url_pattern in url_resolver.url_patterns], ['forum/<int:post_id>'])

    def test_urls__routes_page__when_only_discovery_imports_its_module(self):
        self.write_page_module('nested_page/__init__.py', '')
        self.write_page_module(
            'nested_page/nested_page.py',
            'from website_widgets import WebPage, register_url\n'
            '\n'
            '\n'
            "@register_url('nested', name='nested')\n"
            'class NestedPage(WebPage):\n'
            '    pass\n')

        self.assertEqual(self.get_routes_in_url_order(), ['nested'])

    def test_urls__orders_fixed_segment_first__when_parameter_could_match_it(self):
        @register_url('profile/<str:username>', name='profile')
        class ProfilePage(WebPage):
            pass

        @register_url('profile/settings', name='profile_settings')
        class SettingsPage(WebPage):
            pass

        self.assertEqual(self.get_routes_in_url_order(), ['profile/settings', 'profile/<str:username>'])

    def test_urls__orders_longer_route_first__when_path_parameter_could_match_it(self):
        @register_url('files/<path:file_path>', name='file')
        class FilePage(WebPage):
            pass

        @register_url('files/<path:file_path>/history', name='file_history')
        class FileHistoryPage(WebPage):
            pass

        self.assertEqual(
            self.get_routes_in_url_order(),
            ['files/<path:file_path>/history', 'files/<path:file_path>'])

    def test_urls__orders_alphabetically__when_routes_are_equally_specific(self):
        @register_url('tabs/<int:tab_id>', name='tab')
        class TabPage(WebPage):
            pass

        @register_url('forum/<int:post_id>', name='forum_post')
        class ForumPostPage(WebPage):
            pass

        self.assertEqual(self.get_routes_in_url_order(), ['forum/<int:post_id>', 'tabs/<int:tab_id>'])
