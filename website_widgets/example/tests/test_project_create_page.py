from django.urls import reverse

from website_widgets.example.tests.example_test_case import ExampleTestCase


class ProjectCreatePageTestCase(ExampleTestCase):
    def test_project_create_page__fails__when_anonymous(self):
        self.assertEqual(self.client.get(reverse('website_widgets_example_project_create')).status_code, 401)

    def test_project_create_page__succeeds__when_user(self):
        self.log_in_as(self.USER_2)

        self.assertEqual(self.client.get(reverse('website_widgets_example_project_create')).status_code, 200)
