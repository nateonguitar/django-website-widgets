import io

from django.core.management import CommandError, call_command
from django.urls import path

from website_widgets import PageRoutes, register_url
from website_widgets.page import Page
from website_widgets.tests.page_routes.page_routes_test_case import PageRoutesTestCase
from website_widgets.tests.sample_widgets import UnsetDocumentPage


class ShowPageResolveOrderTestCase(PageRoutesTestCase):
    def run_show_page_resolve_order(self, *args, output: io.StringIO | None = None, **options) -> str:
        output = output or io.StringIO()
        call_command('show_page_resolve_order', *args, stdout=output, no_color=True, **options)
        return output.getvalue()

    def test_show_page_resolve_order__shows_only_given_columns__when_columns_given(self):
        @register_url('forum/<int:post_id>', name='forum_post')
        class ForumPostPage(Page):
            pass

        self.use_urlconf([path('', PageRoutes.urls())])

        output = self.run_show_page_resolve_order('--columns=url,name')

        self.assertIn('website:forum_post', output)
        self.assertNotIn('ForumPostPage', output)

    def test_show_page_resolve_order__lists_unreachable_route__when_reaches_page_column_hidden(self):
        @register_url('profile/<str:username>', name='profile')
        class ProfilePage(Page):
            pass

        self.use_urlconf([
            path('profile/<str:username>', UnsetDocumentPage.as_view(), name='hand_routed_profile'),
            path('', PageRoutes.urls()),
        ])
        output = io.StringIO()

        with self.assertRaises(CommandError):
            self.run_show_page_resolve_order('--columns=url', output=output)

        self.assertIn('/profile/a goes to hand_routed_profile instead', output.getvalue())

    def test_show_page_resolve_order__shows_converter_only__when_path_param_type_is_type(self):
        @register_url('forum/<int:post_id>', name='forum_post')
        class ForumPostPage(Page):
            pass

        self.use_urlconf([path('', PageRoutes.urls())])

        output = self.run_show_page_resolve_order(path_param_type='type')

        self.assertIn('/forum/<int>', output)

    def test_show_page_resolve_order__shows_sample_value__when_path_param_type_is_example(self):
        @register_url('forum/<int:post_id>', name='forum_post')
        class ForumPostPage(Page):
            pass

        self.use_urlconf([path('', PageRoutes.urls())])

        output = self.run_show_page_resolve_order(path_param_type='example')

        self.assertIn('/forum/1 ', output)

    def test_show_page_resolve_order__lists_fixed_segment_first__when_parameter_could_match_it(self):
        @register_url('profile/<str:username>', name='profile')
        class ProfilePage(Page):
            pass

        @register_url('profile/settings', name='profile_settings')
        class SettingsPage(Page):
            pass

        self.use_urlconf([path('', PageRoutes.urls())])

        output = self.run_show_page_resolve_order()

        self.assertLess(output.index('profile/settings'), output.index('profile/<str:username>'))

    def test_show_page_resolve_order__fails__when_earlier_urlconf_route_takes_its_url(self):
        @register_url('profile/<str:username>', name='profile')
        class ProfilePage(Page):
            pass

        self.use_urlconf([
            path('profile/<str:username>', UnsetDocumentPage.as_view(), name='hand_routed_profile'),
            path('', PageRoutes.urls()),
        ])

        with self.assertRaises(CommandError):
            self.run_show_page_resolve_order()

    def test_show_page_resolve_order__fails__when_page_routes_not_included(self):
        @register_url('profile/<str:username>', name='profile')
        class ProfilePage(Page):
            pass

        self.use_urlconf([])

        with self.assertRaises(CommandError):
            self.run_show_page_resolve_order()
