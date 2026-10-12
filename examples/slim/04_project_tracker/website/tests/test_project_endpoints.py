from django.urls import reverse

from website.models import Project
from website.tests.tracker_test_case import TrackerTestCase


class ProjectEndpointsTestCase(TrackerTestCase):
    def project_url(self, project: Project) -> str:
        return reverse('api_project', kwargs={'project_id': project.pk})

    def test_get_project__succeeds__when_creator(self):
        self.log_in_as(self.USER_1)

        response = self.client.get(self.project_url(self.project_named('Garden planner')))

        self.assertEqual(response.json()['created_by_name'], 'Riley Park')

    def test_get_project__fails__when_another_user(self):
        self.log_in_as(self.USER_2)

        response = self.client.get(self.project_url(self.project_named('Garden planner')))

        self.assertEqual(response.status_code, 403)

    def test_get_project__fails__when_missing(self):
        self.log_in_as(self.ADMIN)

        response = self.client.get(reverse('api_project', kwargs={'project_id': 999}))

        self.assertEqual(response.status_code, 404)

    def test_update_project__changes_only_given_fields__when_creator(self):
        project = self.project_named('Garden planner')
        self.log_in_as(self.USER_1)

        response = self.send_json('patch', self.project_url(project), {'name': 'Vegetable garden'})

        project.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(project.name, 'Vegetable garden')
        self.assertEqual(project.description, 'Which vegetables go in which bed, and when to plant them.')

    def test_update_project__succeeds__when_staff(self):
        self.log_in_as(self.ADMIN)

        response = self.send_json('patch', self.project_url(self.project_named('Reading list')), {'description': ''})

        self.assertEqual(response.json()['description'], '')

    def test_delete_project__succeeds__when_creator(self):
        project = self.project_named('Garden planner')
        self.log_in_as(self.USER_1)

        response = self.client.delete(self.project_url(project))

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Project.objects.filter(pk=project.pk).exists())

    def test_delete_project__fails__when_another_user(self):
        project = self.project_named('Garden planner')
        self.log_in_as(self.USER_2)

        response = self.client.delete(self.project_url(project))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Project.objects.filter(pk=project.pk).exists())
