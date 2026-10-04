from django.urls import reverse

from website_widgets.example.projects.store import Project
from website_widgets.example.tests.example_test_case import ExampleTestCase


class ProjectsPostEndpointTestCase(ExampleTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse('website_widgets_example_api_projects')

    def test_create_project__succeeds__when_user(self):
        self.log_in_as(self.USER_2)

        response = self.send_json('post', self.url, {
            'name': '  Trip plan  ',
            'description': 'Where to go.',
        })

        self.assertEqual(response.status_code, 201)
        project = response.json()
        self.assertEqual(project['name'], 'Trip plan')
        self.assertEqual(project['created_by'], self.USER_2)
        self.assertContains(self.client.get(project['url']), 'Trip plan')

    def test_create_project__makes_admin_the_owner__when_admin(self):
        self.log_in_as(self.ADMIN)

        response = self.send_json('post', self.url, {
            'name': 'Admin notes',
        })

        self.assertEqual(response.json()['created_by'], self.ADMIN)

    def test_create_project__ignores_read_only_fields__when_sent(self):
        self.log_in_as(self.USER_2)

        response = self.send_json('post', self.url, {
            'name': 'Trip plan',
            'id': 1,
            'created_by': self.USER_1,
        })

        project = response.json()
        self.assertEqual(project['id'], 3)
        self.assertEqual(project['created_by'], self.USER_2)

    def test_create_project__fails__when_anonymous(self):
        response = self.send_json('post', self.url, {
            'name': 'Trip plan',
        })

        self.assertEqual(response.status_code, 401)

    def test_create_project__fails__when_name_missing(self):
        self.log_in_as(self.USER_1)

        response = self.send_json('post', self.url, {
            # 'name': 'Trip plan',
            'description': 'Where to go.',
        })

        self.assertEqual(response.status_code, 422)
        self.assertEqual(list(response.json()['errors']), ['name'])

    def test_create_project__fails__when_description_too_long(self):
        self.log_in_as(self.USER_1)

        response = self.send_json('post', self.url, {
            'name': 'Trip plan',
            'description': 'x' * (Project.DESCRIPTION_MAX_LENGTH + 1),
        })

        self.assertEqual(response.status_code, 422)
        self.assertEqual(list(response.json()['errors']), ['description'])
