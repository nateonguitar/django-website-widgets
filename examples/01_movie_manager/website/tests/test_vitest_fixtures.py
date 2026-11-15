from pathlib import Path
from unittest import mock

from bs4 import BeautifulSoup
from django.test import tag
from django.urls import reverse

from api.models import Copy, Genre, Movie, MovieRating, User
from website.tests.app_widget_test_case import AppWidgetTestCase
from website.widgets.movie_card import MovieCard


@tag('vitest_fixtures')
class VitestFixturesTestCase(AppWidgetTestCase):
    """
    The HTML the Vitest tests mount their controllers on, rendered here by the same Python that
    renders it for a browser, so a template change reaches the JS tests instead of a hand-copied
    fragment drifting from it. Ordinary tests that also write a file: `npm test` runs them first
    (`manage.py test --tag=vitest_fixtures`, from `vitest.global-setup.ts`), and a plain
    `manage.py test` runs them too.
    """

    # Git-ignored. `tests/fixtures.ts` reads from the same folder.
    FIXTURES_DIR = Path(__file__).resolve().parent.parent / 'vitest_fixtures'

    @classmethod
    def setUpTestData(cls):
        cls.alex = User.objects.get(username='alex')
        cls.paddington = Movie.objects.create(title='Paddington', year=2014, genre=Genre.FAMILY, rating=MovieRating.PG)
        Copy.objects.create_copies(cls.paddington, 1)

    def write_fixture(self, name: str, html: str):
        self.FIXTURES_DIR.mkdir(exist_ok=True)
        (self.FIXTURES_DIR / name).write_text(html)

    async def test_fixture__movie_card_beside_the_appbar__when_signed_in(self):
        movies = Movie.objects.with_availability()
        movie = await movies.aget(id=self.paddington.id)
        movie_card = MovieCard(movie=movie, key=movie.id)

        html = await self.arender_document(movie_card, user=self.alex)

        soup = BeautifulSoup(html, 'html.parser')
        appbar = soup.select_one('#appbar')
        confirm_dialog_template = soup.select_one('#confirm-dialog-template')
        self.assertIsNotNone(appbar)
        self.assertIsNotNone(confirm_dialog_template)
        self.write_fixture('movie_card__signed_in.html', html)

    def test_fixture__cart_page__when_signed_in(self):
        self.client.force_login(self.alex)
        cart_url = reverse('website:CartPage')

        response = self.client.get(cart_url)

        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.write_fixture('cart_page.html', html)

    def test_fixture__find_page_and_a_search_answer__when_searched(self):
        find_url = reverse('website:FindMoviePage')
        search_url = reverse('api:search_movies')

        page = self.client.get(find_url)
        # The endpoint waits so a spinner shows on a local machine; nothing here needs to see it.
        with mock.patch('api.endpoints.movies.endpoint_search_movies.SEARCH_DELAY_SECONDS', 0):
            answer = self.client.get(search_url, {'q': 'Paddington'})

        page_html = page.content.decode()
        answer_html = answer.content.decode()
        self.assertEqual(page.status_code, 200)
        self.assertEqual(answer.status_code, 200)
        self.assertIn('Paddington', answer_html)
        self.write_fixture('find_movie_page.html', page_html)
        self.write_fixture('find_movie_page__search_answer.html', answer_html)
