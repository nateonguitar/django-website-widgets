from django.urls import reverse

from website_widgets.example.projects.viewer_cookie import ViewerCookie
from website_widgets.example.tests.example_test_case import ExampleTestCase


class LoginPostEndpointTestCase(ExampleTestCase):
    def log_in(self, data):
        return self.send_json('post', reverse('website_widgets_example_api_login'), data)

    def test_login__succeeds__when_username_known(self):
        response = self.log_in({
            'username': 'user_2',
            'password': 'anything',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['name'], 'Jordan Avery')
        self.assertEqual(response.cookies[ViewerCookie.NAME].value, '2')

    def test_login__fails__when_username_unknown(self):
        response = self.log_in({
            'username': 'nobody',
            'password': 'anything',
        })

        self.assertEqual(response.status_code, 422)
        self.assertIn('username', response.json()['errors'])
        self.assertNotIn(ViewerCookie.NAME, response.cookies)

    def test_login__fails__when_username_missing(self):
        response = self.log_in({
            'password': 'anything',
        })

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['errors'], {'username': ['The username is required.']})

    def test_login__fails__when_username_null(self):
        response = self.log_in({
            'username': None,
        })

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['errors'], {'username': ['The username is required.']})

    def test_login__returns_next__when_local_path(self):
        response = self.log_in({
            'username': 'user_1',
            'next': '/projects/1/',
        })

        self.assertEqual(response.json()['next'], '/projects/1/')

    def test_login__ignores_next__when_another_site(self):
        for next_url in ('https://evil.example.com/', '//evil.example.com/', 'javascript:alert(1)'):
            with self.subTest(next_url=next_url):
                response = self.log_in({
                    'username': 'user_1',
                    'next': next_url,
                })

                self.assertEqual(response.json()['next'], reverse('website_widgets_example_projects'))
