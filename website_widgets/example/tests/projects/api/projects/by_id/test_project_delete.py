from website_widgets.example.tests.projects.api.projects.by_id.project_endpoint_test_case import ProjectEndpointTestCase


class ProjectDeleteEndpointTestCase(ProjectEndpointTestCase):
    def test_delete_project__succeeds__when_creator(self):
        self.log_in_as(self.USER_1)

        response = self.client.delete(self.project_url(1))

        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.client.get(self.page_url(1)).status_code, 404)

    def test_delete_project__succeeds__when_admin(self):
        self.log_in_as(self.ADMIN)

        self.assertEqual(self.client.delete(self.project_url(2)).status_code, 204)

    def test_delete_project__fails__when_another_user(self):
        self.log_in_as(self.USER_2)

        self.assertEqual(self.client.delete(self.project_url(1)).status_code, 403)

    def test_delete_project__fails__when_anonymous(self):
        self.assertEqual(self.client.delete(self.project_url(1)).status_code, 401)

    def test_delete_project__fails__when_missing(self):
        self.log_in_as(self.USER_1)

        self.assertEqual(self.client.delete(self.project_url(99)).status_code, 404)
