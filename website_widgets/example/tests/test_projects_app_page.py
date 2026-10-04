from django.urls import reverse

from website_widgets.example.projects.flash_cookie import FlashCookie
from website_widgets.example.tests.example_test_case import ExampleTestCase


class ProjectsAppPageTestCase(ExampleTestCase):
    """The projects app base page's shared behaviour, exercised through the login page."""

    def test_viewer__renders_name__when_logged_in(self):
        self.log_in_as(self.USER_1)

        response = self.client.get(reverse('website_widgets_example_login'))

        self.assertContains(response, 'Riley Park')

    def test_viewer__renders_log_in_link__when_cookie_names_no_user(self):
        self.client.cookies['website_widgets_example_user'] = '999'

        response = self.client.get(reverse('website_widgets_example_login'))

        self.assertNotContains(response, 'Log out')
        self.assertContains(response, 'id="example-login-form"')

    def test_appbar__renders__when_rendered(self):
        response = self.client.get(reverse('website_widgets_example_login'))

        self.assertContains(response, 'id="example-appbar"')

    def test_head__renders_page_title_and_description__when_rendered(self):
        response = self.client.get(reverse('website_widgets_example_login'))

        self.assertContains(response, '<title>Log in | website_widgets example</title>', html=False)
        self.assertContains(response, '<meta name="description" content="Log in to the example site')

    def test_store_warning__renders__when_rendered(self):
        response = self.client.get(reverse('website_widgets_example_login'))

        self.assertContains(response, 'wiped when the Django server restarts')

    def test_flash__renders_message_once__when_cookie_set(self):
        self.client.cookies[FlashCookie.NAME] = 'Project%20created.'

        first = self.client.get(reverse('website_widgets_example_login'))
        second = self.client.get(reverse('website_widgets_example_login'))

        self.assertContains(first, 'Project created.')
        self.assertNotContains(second, 'Project created.')

    def test_flash__renders_escaped__when_cookie_holds_markup(self):
        self.client.cookies[FlashCookie.NAME] = '%3Cscript%3Ebad()%3C%2Fscript%3E'

        response = self.client.get(reverse('website_widgets_example_login'))

        self.assertNotContains(response, '<script>bad()</script>', html=False)
        self.assertContains(response, '&lt;script&gt;bad()&lt;/script&gt;', html=False)

    def test_unauthorized__renders_login_link_keeping_path__when_anonymous(self):
        response = self.client.get(reverse('website_widgets_example_projects') + '?sort=name')

        self.assertContains(
            response,
            '/projects/login/?next=%2Fprojects%2F%3Fsort%3Dname',
            status_code=401)
