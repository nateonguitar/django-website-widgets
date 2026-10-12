from django.urls import reverse

from website.tests.tracker_test_case import TrackerTestCase


class LoginEndpointTestCase(TrackerTestCase):
    def log_in(self, data: dict):
        return self.send_json('post', reverse('api_login'), data)

    def test_login__starts_session__when_password_matches(self):
        response = self.log_in({'username': 'user_2', 'password': 'try-the-widgets'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['name'], 'Jordan Avery')
        self.assertEqual(self.client.get(reverse('website:ProjectsPage')).status_code, 200)

    def test_login__fails_on_password_field__when_password_is_wrong(self):
        response = self.log_in({'username': 'user_2', 'password': 'nope'})

        self.assertEqual(response.status_code, 422)
        self.assertIn('password', response.json()['errors'])

    def test_login__fails__when_fields_missing(self):
        response = self.log_in({})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(set(response.json()['errors']), {'username', 'password'})

    def test_login__returns_projects_page__when_next_is_offsite(self):
        for next_url in ('https://evil.example.com/', '//evil.example.com/', 'javascript:alert(1)'):
            with self.subTest(next_url=next_url):
                response = self.log_in({'username': 'user_1', 'password': 'try-the-widgets', 'next': next_url})

                self.assertEqual(response.json()['next'], reverse('website:ProjectsPage'))

    def test_logout__ends_session__when_logged_in(self):
        self.log_in_as(self.USER_1)

        self.client.post(reverse('api_logout'))

        self.assertEqual(self.client.get(reverse('website:ProjectsPage')).status_code, 401)
