from django.urls import reverse

from website_widgets.example.tests.example_test_case import ExampleTestCase


class WidgetFromEndpointPageTestCase(ExampleTestCase):
    def test_widget_from_endpoint_page__renders_only_tip_zero__when_rendered(self):
        response = self.client.get(reverse('website_widgets_example_widget_from_endpoint'))

        self.assertContains(response, 'class="example-card example-tip"', count=1)
        self.assertContains(response, 'data-tip-number="0"')

    def test_widget_from_endpoint_page__renders_load_button__when_rendered(self):
        response = self.client.get(reverse('website_widgets_example_widget_from_endpoint'))

        self.assertContains(response, 'id="example-widget-from-endpoint-load"')
        self.assertContains(response, reverse('website_widgets_example_api_tip'))
