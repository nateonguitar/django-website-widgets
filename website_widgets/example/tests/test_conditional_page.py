from django.urls import reverse

from website_widgets.example.tests.example_test_case import ExampleTestCase


class ConditionalPageTestCase(ExampleTestCase):
    def test_conditional_page__shows_etag__when_rendered(self):
        response = self.client.get(reverse('website_widgets_example_conditional') + '?version=2')

        self.assertEqual(response['ETag'], '"example-v2"')
        self.assertContains(response, '&quot;example-v2&quot;')

    def test_conditional_page__returns_not_modified__when_etag_matches(self):
        response = self.client.get(
            reverse('website_widgets_example_conditional') + '?version=2',
            headers={'If-None-Match': '"example-v2"'})

        self.assertEqual(response.status_code, 304)

    def test_conditional_page__returns_full_page__when_version_changed(self):
        response = self.client.get(
            reverse('website_widgets_example_conditional') + '?version=3',
            headers={'If-None-Match': '"example-v2"'})

        self.assertEqual(response.status_code, 200)
