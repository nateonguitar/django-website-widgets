from website_widgets.example.tests.projects.api.projects.by_id.project_endpoint_test_case import ProjectEndpointTestCase


class ProjectGetEndpointTestCase(ProjectEndpointTestCase):
    def test_get_project__succeeds__when_creator(self):
        self.log_in_as(self.USER_1)

        response = self.client.get(self.project_url(1))

        self.assertEqual(response.json()['name'], 'Garden planner')

    def test_get_project__fails__when_anonymous(self):
        self.assertEqual(self.client.get(self.project_url(1)).status_code, 401)

    def test_get_project__fails__when_another_user(self):
        self.log_in_as(self.USER_2)

        self.assertEqual(self.client.get(self.project_url(1)).status_code, 403)

    def test_get_project__fails__when_missing(self):
        self.log_in_as(self.USER_1)

        self.assertEqual(self.client.get(self.project_url(99)).status_code, 404)
