from django.test import TestCase

from api.models import User


class SignOutTestCase(TestCase):
    def test_sign_out__succeeds_ending_the_session__when_signed_in(self):
        self.client.force_login(User.objects.get(username='alex'))

        response = self.client.post('/api/auth/sign-out')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'redirect': '/'})
        self.assertEqual(self.client.get('/cart').status_code, 401)

    def test_sign_out__fails__when_signed_out(self):
        response = self.client.post('/api/auth/sign-out')

        self.assertEqual(response.status_code, 401)

    def test_sign_out__fails__when_requested_with_get(self):
        self.client.force_login(User.objects.get(username='alex'))

        response = self.client.get('/api/auth/sign-out')

        self.assertEqual(response.status_code, 405)
