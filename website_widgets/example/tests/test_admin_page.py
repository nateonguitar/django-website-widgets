from django.urls import reverse

from website_widgets.example.tests.example_test_case import ExampleTestCase


class AdminPageTestCase(ExampleTestCase):
    def test_admin_page__fails__when_anonymous(self):
        self.assertEqual(self.client.get(reverse('website_widgets_example_admin')).status_code, 401)

    def test_admin_page__fails__when_regular_user(self):
        self.log_in_as(self.USER_1)

        self.assertEqual(self.client.get(reverse('website_widgets_example_admin')).status_code, 403)

    def test_admin_page__succeeds__when_admin(self):
        self.log_in_as(self.ADMIN)

        response = self.client.get(reverse('website_widgets_example_admin'))

        self.assertContains(response, 'Jordan Avery')
