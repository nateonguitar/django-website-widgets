from django.urls import reverse

from website_widgets.example.projects.store import Store
from website_widgets.example.tests.example_test_case import ExampleTestCase


class ProjectsPageTestCase(ExampleTestCase):
    def test_projects_page__fails__when_anonymous(self):
        self.assertEqual(self.client.get(reverse('website_widgets_example_projects')).status_code, 401)

    def test_projects_page__lists_own_projects__when_user(self):
        self.log_in_as(self.USER_1)

        response = self.client.get(reverse('website_widgets_example_projects'))

        self.assertContains(response, 'Garden planner')
        self.assertNotContains(response, 'Reading list')

    def test_projects_page__lists_every_project__when_admin(self):
        self.log_in_as(self.ADMIN)

        response = self.client.get(reverse('website_widgets_example_projects'))

        self.assertContains(response, 'Garden planner')
        self.assertContains(response, 'Reading list')

    def test_projects_page__shows_creator_on_each_tile__when_admin(self):
        self.log_in_as(self.ADMIN)

        response = self.client.get(reverse('website_widgets_example_projects'))

        self.assertContains(response, 'By Riley Park')
        self.assertContains(response, 'By Jordan Avery')

    def test_projects_page__shows_empty_state__when_user_has_no_projects(self):
        Store.delete_project(Store.find_project(1))
        self.log_in_as(self.USER_1)

        response = self.client.get(reverse('website_widgets_example_projects'))

        self.assertContains(response, 'No projects yet.')
