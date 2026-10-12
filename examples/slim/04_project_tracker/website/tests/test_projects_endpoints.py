from django.urls import reverse

from website.models import Project
from website.tests.tracker_test_case import TrackerTestCase


class ProjectsEndpointsTestCase(TrackerTestCase):
    def test_list_projects__fails__when_anonymous(self):
        self.assertEqual(self.client.get(reverse('api_projects')).status_code, 401)

    def test_list_projects__returns_own__when_user(self):
        self.log_in_as(self.USER_2)

        response = self.client.get(reverse('api_projects'))

        self.assertEqual([project['name'] for project in response.json()], ['Reading list'])

    def test_list_projects__returns_every_project__when_staff(self):
        self.log_in_as(self.ADMIN)

        response = self.client.get(reverse('api_projects'))

        self.assertEqual(len(response.json()), Project.objects.count())

    def test_create_project__succeeds_owned_by_viewer__when_valid(self):
        self.log_in_as(self.USER_2)

        response = self.send_json('post', reverse('api_projects'), {'name': '  Trip  ', 'description': 'Where to go.'})

        self.assertEqual(response.status_code, 201)
        project = Project.objects.get(pk=response.json()['id'])
        self.assertEqual((project.name, project.created_by.username), ('Trip', 'user_2'))

    def test_create_project__fails_listing_errors_by_field__when_invalid(self):
        self.log_in_as(self.USER_1)

        response = self.send_json('post', reverse('api_projects'), {'name': '', 'description': 7})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json(), {
            'errors': {
                'name': ['The name is required.'],
                'description': ['The description must be text.'],
            },
        })

    def test_route__fails_listing_allowed_methods__when_no_endpoint_for_method(self):
        response = self.client.put(reverse('api_projects'))

        self.assertEqual(response.status_code, 405)
        self.assertEqual(response['Allow'], 'GET, POST')
