from django.urls import reverse

from website.flash_cookie import FlashCookie
from website.tests.tracker_test_case import TrackerTestCase


class ProjectsPageTestCase(TrackerTestCase):
    def test_projects_page__renders_unauthorized_variant__when_anonymous(self):
        response = self.client.get(reverse('website:ProjectsPage'))

        self.assertContains(response, 'example-access-unauthorized', status_code=401)
        self.assertContains(response, f'{reverse("website:LoginPage")}?next=', status_code=401)

    def test_projects_page__lists_own_projects_with_creator__when_user(self):
        self.log_in_as(self.USER_1)

        response = self.client.get(reverse('website:ProjectsPage'))

        self.assertContains(response, 'Garden planner')
        self.assertContains(response, 'By Riley Park')
        self.assertNotContains(response, 'Reading list')

    def test_projects_page__shows_flash_message_once__when_cookie_set(self):
        self.log_in_as(self.USER_1)
        self.client.cookies[FlashCookie.NAME] = 'Project%20created.'

        response = self.client.get(reverse('website:ProjectsPage'))

        self.assertContains(response, 'Project created.')
        self.assertEqual(response.cookies[FlashCookie.NAME].value, '')


class ProjectPageTestCase(TrackerTestCase):
    def project_url(self, project_id: int) -> str:
        return reverse('website:ProjectPage', kwargs={'project_id': project_id})

    def test_project_page__puts_project_in_head__when_creator(self):
        project = self.project_named('Garden planner')
        self.log_in_as(self.USER_1)

        response = self.client.get(self.project_url(project.pk))

        self.assertContains(response, '<title>Garden planner | Project tracker</title>', html=False)

    def test_project_page__renders_forbidden_variant__when_another_user(self):
        self.log_in_as(self.USER_2)

        response = self.client.get(self.project_url(self.project_named('Garden planner').pk))

        self.assertContains(response, 'example-access-forbidden', status_code=403)
        self.assertNotContains(response, 'Which vegetables', status_code=403)

    def test_project_page__renders_not_found_variant__when_missing(self):
        self.log_in_as(self.USER_1)

        response = self.client.get(self.project_url(999))

        self.assertContains(response, 'example-access-not-found', status_code=404)


class TeamPageTestCase(TrackerTestCase):
    def test_team_page__renders_forbidden_variant__when_not_staff(self):
        self.log_in_as(self.USER_1)

        self.assertEqual(self.client.get(reverse('website:TeamPage')).status_code, 403)

    def test_team_page__counts_each_users_projects__when_staff(self):
        self.log_in_as(self.ADMIN)

        response = self.client.get(reverse('website:TeamPage'))

        self.assertContains(response, 'Riley Park')
        self.assertContains(response, '<td>1</td>', count=2, html=False)


class LoginPageTestCase(TrackerTestCase):
    def test_login_page__lists_demo_users__when_anonymous(self):
        response = self.client.get(reverse('website:LoginPage'))

        for username in ('user_1', 'user_2', 'admin'):
            self.assertContains(response, username)

    def test_login_page__renders_already_logged_in_variant__when_logged_in(self):
        self.log_in_as(self.USER_2)

        response = self.client.get(reverse('website:LoginPage'))

        self.assertContains(response, "You're already logged in as Jordan Avery.", html=False)

    def test_document__links_static_files_and_hands_them_their_values__when_rendered(self):
        response = self.client.get(reverse('website:LoginPage'))

        self.assertContains(response, 'href="/static/website/styles.css"')
        self.assertContains(response, 'src="/static/website/api.js"')
        self.assertContains(response, f'<meta name="flash-cookie-name" content="{FlashCookie.NAME}">', html=False)
        self.assertContains(response, '<meta name="csrf-token" content="', html=False)
