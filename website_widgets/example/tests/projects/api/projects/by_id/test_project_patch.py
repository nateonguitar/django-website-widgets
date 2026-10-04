from website_widgets.example.projects.store import Store
from website_widgets.example.tests.projects.api.projects.by_id.project_endpoint_test_case import ProjectEndpointTestCase


class ProjectPatchEndpointTestCase(ProjectEndpointTestCase):
    def test_update_project__succeeds__when_creator(self):
        self.log_in_as(self.USER_1)

        response = self.send_json('patch', self.project_url(1), {
            'name': 'Vegetable garden',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['name'], 'Vegetable garden')
        self.assertContains(self.client.get(self.page_url(1)), 'Vegetable garden')

    def test_update_project__keeps_omitted_fields__when_partial(self):
        self.log_in_as(self.USER_1)

        response = self.send_json('patch', self.project_url(1), {
            'name': 'Vegetable garden',
        })

        self.assertTrue(response.json()['description'].startswith('Which vegetables'))

    def test_update_project__keeps_field__when_sent_null(self):
        self.log_in_as(self.USER_1)

        response = self.send_json('patch', self.project_url(1), {
            'name': None,
        })

        self.assertEqual(response.json()['name'], 'Garden planner')

    def test_update_project__ignores_read_only_fields__when_sent(self):
        self.log_in_as(self.USER_1)

        response = self.send_json('patch', self.project_url(1), {
            'id': 2,
            'created_by': 2,
        })

        self.assertEqual(response.json()['id'], 1)
        self.assertEqual(Store.find_project(1).created_by, self.USER_1)

    def test_update_project__succeeds__when_admin(self):
        self.log_in_as(self.ADMIN)

        response = self.send_json('patch', self.project_url(2), {
            'description': 'Edited by the admin.',
        })

        self.assertEqual(response.status_code, 200)

    def test_update_project__fails__when_another_user(self):
        self.log_in_as(self.USER_2)

        response = self.send_json('patch', self.project_url(1), {
            'name': 'Mine now',
        })

        self.assertEqual(response.status_code, 403)

    def test_update_project__fails__when_anonymous(self):
        response = self.send_json('patch', self.project_url(1), {
            'name': 'Mine now',
        })

        self.assertEqual(response.status_code, 401)

    def test_update_project__fails__when_missing(self):
        self.log_in_as(self.USER_1)

        response = self.send_json('patch', self.project_url(99), {
            'name': 'Ghost',
        })

        self.assertEqual(response.status_code, 404)

    def test_update_project__fails_leaving_project_unchanged__when_name_blank(self):
        self.log_in_as(self.USER_1)

        response = self.send_json('patch', self.project_url(1), {
            'name': '',
            'description': 'Not saved.',
        })

        self.assertEqual(response.status_code, 422)
        self.assertEqual(list(response.json()['errors']), ['name'])
        self.assertEqual(Store.find_project(1).name, 'Garden planner')
        self.assertNotEqual(Store.find_project(1).description, 'Not saved.')
