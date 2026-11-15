from django.core.exceptions import ImproperlyConfigured

from website_widgets import PageRoutes, register_url
from website_widgets.web_page import AsyncWebPage
from website_widgets.tests.page_routes.page_routes_test_case import PageRoutesTestCase
from website_widgets.widget import SyncWidget


class RegisterUrlTestCase(PageRoutesTestCase):
    def test_register_url__routes_page_at_each_route__when_stacked(self):
        @register_url('forum/<int:post_id>', name='forum_post')
        @register_url('tab-requests/<int:post_id>', name='tab_request')
        class ForumPostPage(AsyncWebPage):
            pass

        page_urls = PageRoutes.urls()

        pages_by_name = {
            url_pattern.name: url_pattern.callback.view_class
            for url_pattern in page_urls.url_patterns
        }
        expected_pages_by_name = {
            'forum_post': ForumPostPage,
            'tab_request': ForumPostPage,
        }
        self.assertEqual(pages_by_name, expected_pages_by_name)

    def test_register_url__names_route_after_class__when_name_omitted(self):
        @register_url('')
        class HomePage(AsyncWebPage):
            pass

        page_urls = PageRoutes.urls()

        names = [
            url_pattern.name
            for url_pattern in page_urls.url_patterns
        ]
        self.assertEqual(names, ['HomePage'])

    def test_register_url__passes_kwargs_to_route__when_kwargs_given(self):
        @register_url('tab-requests/create', name='tab_request_create', kwargs={'post_type': 'tab_request'})
        class CreatePostPage(AsyncWebPage):
            pass

        page_urls = PageRoutes.urls()

        create_pattern = page_urls.url_patterns[0]
        self.assertEqual(create_pattern.default_args, {'post_type': 'tab_request'})

    def test_register_url__fails__when_name_already_registered(self):
        @register_url('forum', name='forum')
        class ForumPage(AsyncWebPage):
            pass

        with self.assertRaises(ImproperlyConfigured):
            @register_url('other-forum', name='forum')
            class OtherForumPage(AsyncWebPage):
                pass

    def test_register_url__fails__when_class_is_not_a_page(self):
        with self.assertRaises(TypeError):
            @register_url('plain', name='plain')
            class PlainWidget(SyncWidget):
                pass
