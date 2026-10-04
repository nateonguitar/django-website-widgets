from django.urls import reverse

from website_widgets.example.projects.viewer_cookie import ViewerCookie
from website_widgets.example.tests.example_test_case import ExampleTestCase


class LogoutPostEndpointTestCase(ExampleTestCase):
    def test_logout__clears_cookie__when_logged_in(self):
        self.log_in_as(self.USER_1)

        response = self.client.post(reverse('website_widgets_example_api_logout'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.cookies[ViewerCookie.NAME].value, '')

    def test_logout__shows_logged_out_page__when_next_page_loads(self):
        self.log_in_as(self.USER_1)
        self.client.post(reverse('website_widgets_example_api_logout'))

        response = self.client.get(reverse('website_widgets_example_projects'))

        self.assertEqual(response.status_code, 401)
