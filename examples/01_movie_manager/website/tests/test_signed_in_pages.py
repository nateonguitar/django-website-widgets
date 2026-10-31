from bs4 import BeautifulSoup
from django.test import TestCase

from api.models import User


class SignedInPagesTestCase(TestCase):
    """The cart, My movies, My history, Who has what and Add to inventory, which only a signed-in visitor sees."""

    PATHS = ['/cart', '/my-movies', '/my-history', '/who-has-what', '/add-movie']

    def test_signed_in_pages__answer_401_linking_to_sign_in__when_signed_out(self):
        for path in self.PATHS:
            with self.subTest(path=path):
                response = self.client.get(path)

                self.assertEqual(response.status_code, 401)
                soup = BeautifulSoup(response.content, 'html.parser')
                self.assertEqual(soup.select_one('.app-page__refusal a')['href'], f'/sign-in?next={path}')

    def test_signed_in_pages__answer_200__when_signed_in(self):
        self.client.force_login(User.objects.get(username='alex'))

        for path in self.PATHS:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_add_movie_page__picks_the_rating_with_the_rating_picker__when_signed_in(self):
        self.client.force_login(User.objects.get(username='alex'))

        response = self.client.get('/add-movie')

        soup = BeautifulSoup(response.content, 'html.parser')
        picker = soup.select_one('.add-movie-page__new .rating-picker')
        self.assertEqual(picker.select_one('select')['name'], 'rating')
        self.assertIsNone(picker.select_one('option[selected]'))

    def test_my_movies_page__lists_only_your_open_rentals__when_signed_in(self):
        self.client.force_login(User.objects.get(username='jordan'))

        response = self.client.get('/my-movies')

        soup = BeautifulSoup(response.content, 'html.parser')
        # Not sam's Spirited Away.
        titles = [title.get_text(strip=True) for title in soup.select('.my-movies-page__rows .rental-row__title')]
        self.assertEqual(titles, ['Die Hard'])

    def test_my_movies_page__says_nothing_is_out__when_you_have_none(self):
        self.client.force_login(User.objects.get(username='alex'))

        response = self.client.get('/my-movies')

        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertEqual(soup.select('.rental-row'), [])
        self.assertContains(response, "You don't have any movies out.")
