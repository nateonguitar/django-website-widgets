from bs4 import BeautifulSoup
from django.test import TestCase

from api.models import Movie, User


class MoviePageTestCase(TestCase):
    def setUp(self):
        self.die_hard = Movie.objects.get(title='Die Hard')

    def copy_statuses(self, response) -> list[str]:
        """The "Where it is" cell of each copy, its whitespace collapsed."""
        soup = BeautifulSoup(response.content, 'html.parser')
        cells = soup.select('#movie-page .copy-table tbody td:nth-of-type(3)')
        return [' '.join(cell.get_text().split()) for cell in cells]

    def test_movie_page__shows_the_movie_and_each_copy__when_it_exists(self):
        response = self.client.get(f'/movies/{self.die_hard.id}')

        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertEqual(soup.title.get_text(), 'Die Hard | Movie Manager')
        self.assertIsNotNone(soup.select_one(f'.movie-page__card .movie-card[data-key="{self.die_hard.id}"]'))
        self.assertEqual(len(self.copy_statuses(response)), 3)

    def test_movie_page__says_who_has_a_copy__when_signed_in(self):
        self.client.force_login(User.objects.get(username='alex'))

        response = self.client.get(f'/movies/{self.die_hard.id}')

        statuses = self.copy_statuses(response)
        self.assertEqual(statuses.count('On the shelf'), 2)
        self.assertEqual(len([status for status in statuses if status.startswith('Out with jordan for ')]), 1)

    def test_movie_page__says_you__when_you_have_the_copy(self):
        self.client.force_login(User.objects.get(username='jordan'))

        response = self.client.get(f'/movies/{self.die_hard.id}')

        statuses = self.copy_statuses(response)
        self.assertEqual(len([status for status in statuses if status.startswith('Out with you for ')]), 1)

    def test_movie_page__hides_who_has_it__when_signed_out(self):
        response = self.client.get(f'/movies/{self.die_hard.id}')

        self.assertEqual(sorted(self.copy_statuses(response)), ['On the shelf', 'On the shelf', 'Out'])

    def test_movie_page__answers_404_with_the_sites_own_page__when_no_movie_has_the_id(self):
        response = self.client.get('/movies/999999')

        self.assertEqual(response.status_code, 404)
        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertEqual(soup.title.get_text(), 'Not found | Movie Manager')
        self.assertEqual(
            soup.select_one('.app-page__refusal p').get_text(strip=True),
            'No movie has that number. It may have been taken off the shelf.')
