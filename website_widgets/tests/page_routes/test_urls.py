from unittest.mock import patch

from website_widgets import PageRoutes, register_url
from website_widgets.config import WebsiteWidgetsConfig
from website_widgets.page import Page
from website_widgets.tests.page_routes.page_routes_test_case import PageRoutesTestCase


class UrlsTestCase(PageRoutesTestCase):
    def test_urls__namespaces_routes_by_website_app_name__when_included(self):
        config = WebsiteWidgetsConfig(website_app_name='storefront')
        self.enterContext(patch('website_widgets.page_routes.get_config', return_value=config))

        _url_patterns, app_name, namespace = PageRoutes.urls()

        self.assertEqual((app_name, namespace), ('storefront', 'storefront'))

    def test_urls__routes_page__when_only_discovery_imports_its_module(self):
        self.write_page_module('nested_page/__init__.py', '')
        self.write_page_module(
            'nested_page/nested_page.py',
            'from website_widgets import Page, register_url\n'
            '\n'
            '\n'
            "@register_url('nested', name='nested')\n"
            'class NestedPage(Page):\n'
            '    pass\n')

        self.assertEqual(self.get_routes_in_url_order(), ['nested'])

    def test_urls__orders_fixed_segment_first__when_parameter_could_match_it(self):
        @register_url('profile/<str:username>', name='profile')
        class ProfilePage(Page):
            pass

        @register_url('profile/settings', name='profile_settings')
        class SettingsPage(Page):
            pass

        self.assertEqual(self.get_routes_in_url_order(), ['profile/settings', 'profile/<str:username>'])

    def test_urls__orders_longer_route_first__when_path_parameter_could_match_it(self):
        @register_url('files/<path:file_path>', name='file')
        class FilePage(Page):
            pass

        @register_url('files/<path:file_path>/history', name='file_history')
        class FileHistoryPage(Page):
            pass

        self.assertEqual(
            self.get_routes_in_url_order(),
            ['files/<path:file_path>/history', 'files/<path:file_path>'])

    def test_urls__orders_alphabetically__when_routes_are_equally_specific(self):
        @register_url('tabs/<int:tab_id>', name='tab')
        class TabPage(Page):
            pass

        @register_url('forum/<int:post_id>', name='forum_post')
        class ForumPostPage(Page):
            pass

        self.assertEqual(self.get_routes_in_url_order(), ['forum/<int:post_id>', 'tabs/<int:tab_id>'])
