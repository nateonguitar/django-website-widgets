from django.test import SimpleTestCase

from website_widgets.config import WebsiteWidgetsConfig


class WebsiteWidgetsConfigTestCase(SimpleTestCase):
    def test_website_app_name__returns_website__when_not_given(self):
        self.assertEqual(WebsiteWidgetsConfig().website_app_name, 'website')

    def test_website_app_name__returns_given_label__when_given(self):
        config = WebsiteWidgetsConfig(website_app_name='storefront')

        self.assertEqual(config.website_app_name, 'storefront')
