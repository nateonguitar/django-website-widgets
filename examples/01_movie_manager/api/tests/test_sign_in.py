import importlib
import json

from django.test import Client, TestCase


# A migration's module name starts with a digit, so it can't be imported by name.
PASSWORD = importlib.import_module('api.migrations.0002_seed_family_and_movies').PASSWORD


class SignInTestCase(TestCase):
    def sign_in(self, client: Client | None = None, **payload):
        return (client or self.client).post(
            '/api/auth/sign-in',
            data=json.dumps(payload),
            content_type='application/json')

    def test_sign_in__succeeds_redirecting_to_next__when_next_is_on_this_site(self):
        response = self.sign_in(username='alex', password=PASSWORD, next='/cart')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'redirect': '/cart'})
        self.assertEqual(self.client.get('/cart').status_code, 200)

    def test_sign_in__signs_in_to_the_admin_too__when_the_user_is_staff(self):
        self.sign_in(username='sam', password=PASSWORD)

        # One Django session, so the admin needs no second sign-in.
        self.assertEqual(self.client.get('/admin/').status_code, 200)

    def test_sign_in__signs_in_to_the_site__when_signed_in_through_the_admin(self):
        self.client.post('/admin/login/', {'username': 'sam', 'password': PASSWORD})

        self.assertEqual(self.client.get('/cart').status_code, 200)

    def test_sign_in__succeeds_redirecting_to_movies__when_next_is_another_site(self):
        response = self.sign_in(username='alex', password=PASSWORD, next='https://example.com/')

        self.assertEqual(response.json(), {'redirect': '/'})

    def test_sign_in__fails_with_each_field_error__when_fields_are_blank(self):
        response = self.sign_in(username='  ', password='')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {'errors': {'username': 'Enter your username.', 'password': 'Enter your password.'}})

    def test_sign_in__fails_with_a_message__when_password_is_wrong(self):
        response = self.sign_in(username='alex', password='not-it')

        self.assertEqual(response.status_code, 401)
        self.assertIn('message', response.json())
        self.assertEqual(self.client.get('/cart').status_code, 401)

    def test_sign_in__fails__when_csrf_token_is_missing(self):
        client = Client(enforce_csrf_checks=True)

        response = self.sign_in(client, username='alex', password=PASSWORD)

        self.assertEqual(response.status_code, 403)
