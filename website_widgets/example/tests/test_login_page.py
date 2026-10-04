from django.urls import reverse

from website_widgets.example.tests.example_test_case import ExampleTestCase


class LoginPageTestCase(ExampleTestCase):
    def test_login_page__lists_valid_logins__when_anonymous(self):
        response = self.client.get(reverse('website_widgets_example_login'))

        for username in ('user_1', 'user_2', 'admin'):
            self.assertContains(response, username)

    def test_login_page__renders_already_logged_in_variant__when_logged_in(self):
        self.log_in_as(self.USER_2)

        response = self.client.get(reverse('website_widgets_example_login'))

        self.assertContains(response, "You're already logged in as Jordan Avery.")
        self.assertNotContains(response, 'id="example-login-form"')

    def test_login_page__keeps_next__when_given(self):
        response = self.client.get(reverse('website_widgets_example_login') + '?next=/projects/1/')

        self.assertContains(response, 'value="/projects/1/"')
