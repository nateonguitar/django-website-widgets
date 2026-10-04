from django.urls import reverse

from website_widgets.example.tests.example_test_case import ExampleTestCase


class ProjectsGetEndpointTestCase(ExampleTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('website_widgets_example_api_projects')

    def test_list_projects__fails__when_anonymous(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_list_projects__returns_own__when_user(self):
        self.log_in_as(self.USER_2)

        response = self.client.get(self.url)

        self.assertEqual([project['id'] for project in response.json()], [2])

    def test_list_projects__returns_all__when_admin(self):
        self.log_in_as(self.ADMIN)

        response = self.client.get(self.url)

        self.assertEqual([project['id'] for project in response.json()], [1, 2])
