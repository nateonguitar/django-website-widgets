from django.urls import reverse

from website_widgets.example.tests.example_test_case import ExampleTestCase


class IndexPageTestCase(ExampleTestCase):
    def test_index__links_both_apps__when_rendered(self):
        response = self.client.get(reverse('website_widgets_example_index'))

        self.assertContains(response, f'href="{reverse("website_widgets_example_projects")}"')
        self.assertContains(response, f'href="{reverse("website_widgets_example_advanced")}"')

    def test_index__omits_appbar_and_login__when_logged_in(self):
        self.log_in_as(self.USER_1)

        response = self.client.get(reverse('website_widgets_example_index'))

        self.assertNotContains(response, 'id="example-appbar"')
        self.assertNotContains(response, 'Riley Park')
