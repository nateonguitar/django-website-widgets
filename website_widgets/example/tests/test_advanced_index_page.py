from django.urls import reverse

from website_widgets.example.tests.example_test_case import ExampleTestCase


class AdvancedIndexPageTestCase(ExampleTestCase):
    def test_advanced_index__links_every_demo__when_rendered(self):
        response = self.client.get(reverse('website_widgets_example_advanced'))

        for name in ('website_widgets_example_composition', 'website_widgets_example_async','website_widgets_example_widget_from_endpoint', 'website_widgets_example_conditional'):
            self.assertContains(response, f'href="{reverse(name)}"')

    def test_advanced_index__omits_appbar__when_logged_in(self):
        self.log_in_as(self.USER_1)

        response = self.client.get(reverse('website_widgets_example_advanced'))

        self.assertNotContains(response, 'id="example-appbar"')
