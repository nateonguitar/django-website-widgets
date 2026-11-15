from bs4 import BeautifulSoup

from api.models import Genre, Movie
from website.tests.app_widget_test_case import AppWidgetTestCase
from website.widgets.movie_results import MovieResults


class MovieResultsTestCase(AppWidgetTestCase):
    async def render_movie_results(self, movie_results: MovieResults) -> BeautifulSoup:
        html = await self.arender_document(movie_results)
        return BeautifulSoup(html, 'html.parser')

    async def test_movie_results__asks_for_a_search__when_nothing_searched(self):
        movie_results = MovieResults()

        soup = await self.render_movie_results(movie_results)

        prompt_text = soup.select_one('.movie-results__prompt').get_text(strip=True)
        movie_cards = soup.select('.movie-card')
        self.assertEqual(prompt_text, 'Search or pick a category.')
        self.assertEqual(movie_cards, [])

    async def test_movie_results__lists_a_card_per_matching_movie__when_genre_given(self):
        horror_titles = Movie.objects.filter(genre=Genre.HORROR).values_list('title', flat=True)
        expected = [
            title
            async for title in horror_titles
        ]
        movie_results = MovieResults(genre=Genre.HORROR)

        soup = await self.render_movie_results(movie_results)

        titles = [
            title_heading.get_text(strip=True)
            for title_heading in soup.select('.movie-results__grid .movie-card__title')
        ]
        self.assertGreater(len(expected), 0)
        self.assertEqual(titles, expected)

    async def test_movie_results__says_none_match__when_query_finds_nothing(self):
        movie_results = MovieResults(query='no such movie anywhere')

        soup = await self.render_movie_results(movie_results)

        prompt_text = soup.select_one('.movie-results__prompt').get_text(strip=True)
        self.assertEqual(prompt_text, 'No movies match.')
