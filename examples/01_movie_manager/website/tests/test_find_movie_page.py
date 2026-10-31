from bs4 import BeautifulSoup
from django.test import TestCase


class FindMoviePageTestCase(TestCase):
    def test_find_movie_page__shows_the_prompt_and_filters__when_nothing_is_searched(self):
        response = self.client.get('/find')

        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertEqual(soup.title.get_text(), 'Find a movie | Movie Manager')
        self.assertEqual(soup.select_one('.movie-results__prompt').get_text(strip=True), 'Search or pick a category.')
        self.assertIsNotNone(soup.select_one('.find-movie-page__genre option[value="horror"]'))
        self.assertContains(response, "await App.initController(new FindMoviePageController(), '#find-movie-page');")

    def test_find_movie_page__renders_the_results_for_its_url__when_opened_from_a_bookmark(self):
        response = self.client.get('/find', {'genre': 'horror', 'rating': 'R'})

        soup = BeautifulSoup(response.content, 'html.parser')
        # The results are in the page itself, so a bookmark shows them before any script runs.
        titles = [title.get_text(strip=True) for title in soup.select('.movie-card__title')]
        self.assertEqual(titles, ['Alien', 'Get Out', 'Halloween', 'Scream', 'The Shining'])
        # The form shows the same search.
        self.assertEqual(soup.select_one('.find-movie-page__genre option[selected]')['value'], 'horror')
        self.assertEqual(soup.select_one('.find-movie-page__rating option[selected]')['value'], 'R')

    def test_find_movie_page__fills_in_the_title__when_the_url_has_q(self):
        response = self.client.get('/find', {'q': 'die hard'})

        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertEqual(soup.select_one('.find-movie-page__query')['value'], 'die hard')
        titles = [title.get_text(strip=True) for title in soup.select('.movie-card__title')]
        self.assertEqual(titles, ['Die Hard'])

    def test_find_movie_page__treats_unknown_choices_as_any__when_the_url_is_out_of_date(self):
        response = self.client.get('/find', {'genre': 'western', 'rating': 'X'})

        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertEqual(soup.select_one('.movie-results__prompt').get_text(strip=True), 'Search or pick a category.')
        self.assertIsNone(soup.select_one('.find-movie-page__genre option[selected]'))
