from bs4 import BeautifulSoup
from django.test import TestCase

from api.models import User


class SearchMoviesTestCase(TestCase):
    def search(self, **params) -> BeautifulSoup:
        """The endpoint's answer, parsed: the HTML of a MovieResults widget."""
        response = self.client.get('/api/movies/search', params)
        self.assertEqual(response.status_code, 200)
        return BeautifulSoup(response.content, 'html.parser')

    def card_titles(self, soup: BeautifulSoup) -> list[str]:
        return [title.get_text(strip=True) for title in soup.select('.movie-card__title')]

    def test_search_movies__returns_the_prompt__when_nothing_is_searched(self):
        soup = self.search()

        self.assertEqual(soup.select_one('.movie-results__prompt').get_text(strip=True), 'Search or pick a category.')

    def test_search_movies__returns_matching_cards__when_title_matches(self):
        soup = self.search(q='die hard')

        self.assertEqual(self.card_titles(soup), ['Die Hard'])
        # Three copies, one of them out with jordan.
        availability = soup.select_one('.movie-card__availability').get_text(strip=True)
        self.assertEqual(availability, '2 of 3 available')

    def test_search_movies__returns_only_that_genre__when_genre_is_picked(self):
        soup = self.search(genre='horror')

        titles = self.card_titles(soup)
        for title in ('Alien', 'Get Out', 'The Shining'):
            self.assertIn(title, titles)
        self.assertNotIn('Die Hard', titles)

    def test_search_movies__returns_only_that_rating__when_rating_is_picked(self):
        soup = self.search(rating='PG13')

        titles = self.card_titles(soup)
        self.assertIn('Arrival', titles)
        self.assertNotIn('Die Hard', titles)
        for details in soup.select('.movie-card__details'):
            self.assertTrue(details.get_text(strip=True).endswith('PG-13'))

    def test_search_movies__returns_no_match_message__when_nothing_matches(self):
        soup = self.search(q='zzz')

        self.assertEqual(soup.select_one('.movie-results__prompt').get_text(strip=True), 'No movies match.')

    def test_search_movies__shows_none_available__when_every_copy_is_out(self):
        soup = self.search(q='spirited')

        card = soup.select_one('.movie-card')
        self.assertEqual(card.select_one('.movie-card__availability').get_text(strip=True), '0 of 1 available')
        # What the card's controller reads to disable its button.
        self.assertEqual(card['data-available'], '0')

    def test_search_movies__links_to_sign_in__when_signed_out(self):
        soup = self.search(q='die hard')

        card = soup.select_one('.movie-card')
        self.assertEqual(card.select_one('.movie-card__sign-in').get_text(strip=True), 'Sign in to take it')
        self.assertIsNone(card.select_one('.movie-card__action'))

    def test_search_movies__shows_the_cart_button__when_signed_in(self):
        self.client.force_login(User.objects.get(username='alex'))

        soup = self.search(q='die hard')

        card = soup.select_one('.movie-card')
        self.assertIsNotNone(card.select_one('.movie-card__action'))
        self.assertIsNone(card.select_one('.movie-card__sign-in'))

    def test_search_movies__marks_cards_for_choosing__when_purpose_is_choose(self):
        soup = self.search(q='die hard', purpose='choose')

        card = soup.select_one('.movie-card')
        self.assertEqual(card['data-purpose'], 'choose')
        self.assertIsNotNone(card.select_one('.movie-card__action'))

    def test_search_movies__fails__when_genre_is_not_a_choice(self):
        response = self.client.get('/api/movies/search', {'genre': 'western'})

        self.assertEqual(response.status_code, 422)
