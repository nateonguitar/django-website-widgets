import inspect

from django.test import SimpleTestCase

from website_widgets.web_page import AsyncWebPage, SyncWebPage, _WebPage


class PageClassesTestCase(SimpleTestCase):
    def test_async_web_page__fails_at_definition__when_set_context_is_def(self):
        with self.assertRaisesMessage(TypeError, 'AboutPage.set_context() is `def`, but AboutPage is an AsyncWebPage'):
            class AboutPage(AsyncWebPage):
                def set_context(self):
                    pass

    def test_async_web_page__fails_at_definition__when_handle_request_is_def(self):
        with self.assertRaisesMessage(TypeError, 'AboutPage.handle_request() is `def`'):
            class AboutPage(AsyncWebPage):
                def handle_request(self, request, *args, **kwargs):
                    pass

    def test_sync_web_page__fails_at_definition__when_set_context_is_async(self):
        with self.assertRaisesMessage(TypeError, 'AboutPage.set_context() is `async def`, but AboutPage is a SyncWebPage'):
            class AboutPage(SyncWebPage):
                async def set_context(self):
                    pass

    def test_sync_web_page__fails_at_definition__when_build_response_is_async(self):
        with self.assertRaisesMessage(TypeError, 'AboutPage.build_response() is `async def`'):
            class AboutPage(SyncWebPage):
                async def build_response(self):
                    pass

    def test_web_page__fails_at_definition__when_subclassed_directly(self):
        with self.assertRaisesMessage(TypeError, 'subclass AsyncWebPage or SyncWebPage instead'):
            class AboutPage(_WebPage):
                pass

    def test_page_classes__define__when_set_context_left_to_base(self):
        class AsyncAboutPage(AsyncWebPage):
            pass

        class SyncAboutPage(SyncWebPage):
            pass

        self.assertTrue(inspect.iscoroutinefunction(AsyncAboutPage.as_view()))
        self.assertFalse(inspect.iscoroutinefunction(SyncAboutPage.as_view()))
