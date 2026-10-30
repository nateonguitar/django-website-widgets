from bs4 import BeautifulSoup
from django.test import TestCase

from api.models import User


class SignInPageTestCase(TestCase):
    def test_sign_in_page__hands_next_to_the_controller__when_opened_with_next(self):
        response = self.client.get('/sign-in', {'next': '/cart'})

        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertEqual(soup.select_one('#sign-in-page')['data-next'], '/cart')

    def test_sign_in_page__redirects_to_movies__when_already_signed_in(self):
        self.client.force_login(User.objects.get(username='alex'))

        response = self.client.get('/sign-in')

        self.assertRedirects(response, '/')
