import io

from django.core.management import CommandError, call_command
from django.urls import path

from website_widgets import PageRoutes, register_url
from website_widgets.web_page import AsyncWebPage
from website_widgets.tests.page_routes.page_routes_test_case import PageRoutesTestCase
from website_widgets.tests.sample_widgets import UnsetDocumentPage


class WwShowRoutesTestCase(PageRoutesTestCase):
    def run_show_routes(self, *args, output: io.StringIO | None = None, **options) -> str:
        output = output or io.StringIO()
        call_command('ww_show_routes', *args, stdout=output, no_color=True, **options)
        return output.getvalue()

    def use_page_routes_urlconf(self, *earlier_url_patterns):
        """ROOT_URLCONF with the page routes included, after any patterns given."""
        page_urls = PageRoutes.urls()
        page_routes_include = path('', page_urls)
        self.use_urlconf([*earlier_url_patterns, page_routes_include])

    def hand_routed_profile_pattern(self):
        """A route written in urls.py that takes every URL the page route below would."""
        hand_routed_view = UnsetDocumentPage.as_view()
        return path('profile/<str:username>', hand_routed_view, name='hand_routed_profile')

    def test_show_routes__shows_only_given_columns__when_columns_given(self):
        @register_url('forum/<int:post_id>', name='forum_post')
        class ForumPostPage(AsyncWebPage):
            pass

        self.use_page_routes_urlconf()

        output = self.run_show_routes('--columns=url,name')

        self.assertIn('website:forum_post', output)
        self.assertNotIn('ForumPostPage', output)

    def test_show_routes__lists_unreachable_route__when_reaches_page_column_hidden(self):
        @register_url('profile/<str:username>', name='profile')
        class ProfilePage(AsyncWebPage):
            pass

        hand_routed_profile = self.hand_routed_profile_pattern()
        self.use_page_routes_urlconf(hand_routed_profile)
        output = io.StringIO()

        with self.assertRaises(CommandError):
            self.run_show_routes('--columns=url', output=output)

        output_text = output.getvalue()
        self.assertIn('/profile/a goes to hand_routed_profile instead', output_text)

    def test_show_routes__shows_converter_only__when_path_param_type_is_type(self):
        @register_url('forum/<int:post_id>', name='forum_post')
        class ForumPostPage(AsyncWebPage):
            pass

        self.use_page_routes_urlconf()

        output = self.run_show_routes(path_param_type='type')

        self.assertIn('/forum/<int>', output)

    def test_show_routes__shows_sample_value__when_path_param_type_is_example(self):
        @register_url('forum/<int:post_id>', name='forum_post')
        class ForumPostPage(AsyncWebPage):
            pass

        self.use_page_routes_urlconf()

        output = self.run_show_routes(path_param_type='example')

        self.assertIn('/forum/1 ', output)

    def test_show_routes__lists_fixed_segment_first__when_parameter_could_match_it(self):
        @register_url('profile/<str:username>', name='profile')
        class ProfilePage(AsyncWebPage):
            pass

        @register_url('profile/settings', name='profile_settings')
        class SettingsPage(AsyncWebPage):
            pass

        self.use_page_routes_urlconf()

        output = self.run_show_routes()

        settings_position = output.index('profile/settings')
        profile_position = output.index('profile/<str:username>')
        self.assertLess(settings_position, profile_position)

    def test_show_routes__fails__when_earlier_urlconf_route_takes_its_url(self):
        @register_url('profile/<str:username>', name='profile')
        class ProfilePage(AsyncWebPage):
            pass

        hand_routed_profile = self.hand_routed_profile_pattern()
        self.use_page_routes_urlconf(hand_routed_profile)

        with self.assertRaises(CommandError):
            self.run_show_routes()

    def test_show_routes__fails__when_page_routes_not_included(self):
        @register_url('profile/<str:username>', name='profile')
        class ProfilePage(AsyncWebPage):
            pass

        self.use_urlconf([])

        with self.assertRaises(CommandError):
            self.run_show_routes()
