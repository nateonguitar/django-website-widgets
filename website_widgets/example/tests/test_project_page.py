from django.urls import reverse

from website_widgets.example.tests.example_test_case import ExampleTestCase


class ProjectPageTestCase(ExampleTestCase):
    def project_url(self, project_id: int) -> str:
        return reverse('website_widgets_example_project', kwargs={'project_id': project_id})

    def test_project_page__succeeds__when_creator(self):
        self.log_in_as(self.USER_1)

        response = self.client.get(self.project_url(1))

        self.assertContains(response, 'Garden planner')

    def test_project_page__succeeds__when_admin(self):
        self.log_in_as(self.ADMIN)

        self.assertEqual(self.client.get(self.project_url(2)).status_code, 200)

    def test_project_page__fails__when_another_user(self):
        self.log_in_as(self.USER_2)

        response = self.client.get(self.project_url(1))

        self.assertContains(response, '<h1>Forbidden</h1>', status_code=403, html=True)
        self.assertNotContains(response, 'Garden planner', status_code=403)

    def test_project_page__fails__when_anonymous(self):
        response = self.client.get(self.project_url(1))

        self.assertContains(response, '<h1>Unauthorized</h1>', status_code=401, html=True)

    def test_project_page__fails_as_unauthorized__when_anonymous_and_project_missing(self):
        self.assertEqual(self.client.get(self.project_url(99)).status_code, 401)

    def test_project_page__fails__when_project_missing(self):
        self.log_in_as(self.USER_1)

        response = self.client.get(self.project_url(99))

        self.assertContains(response, '<h1>Not Found</h1>', status_code=404, html=True)

    def test_project_page__uses_project_for_head__when_rendered(self):
        self.log_in_as(self.USER_1)

        response = self.client.get(self.project_url(1))

        self.assertContains(response, '<title>Garden planner | website_widgets example</title>', html=False)
        self.assertContains(response, '<meta name="description" content="Which vegetables go in which bed')
