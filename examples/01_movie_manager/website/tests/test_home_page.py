from datetime import timedelta

from bs4 import BeautifulSoup
from django.test import TestCase
from django.utils import timezone

from api.models import Copy, Movie


class HomePageTestCase(TestCase):
    def notes_by_title(self) -> dict[str, str]:
        """Each card's note, by its movie's title, in the order the page lists them."""
        soup = BeautifulSoup(self.client.get('/').content, 'html.parser')
        notes = {}
        for card in soup.select('.home-page__grid .movie-card'):
            title = card.select_one('.movie-card__title').get_text(strip=True)
            notes[title] = card.select_one('.movie-card__note').get_text(strip=True)
        return notes

    def test_home_page__lists_this_months_arrivals_newest_first__when_opened(self):
        titles = list(self.notes_by_title())

        # The seed's arrivals, 5, 9, 12, 18, 20 and 25 days ago.
        self.assertEqual(
            titles,
            ['Toy Story', 'The Iron Giant', 'Die Hard', 'Jurassic Park', 'Paddington', 'Home Alone'])

    def test_home_page__says_brand_new_or_how_many_copies__when_listing_an_arrival(self):
        notes = self.notes_by_title()

        self.assertTrue(notes['Toy Story'].startswith('New to the shelf'))
        self.assertTrue(notes['Die Hard'].startswith('1 new copy'))

    def test_home_page__leaves_out_older_arrivals__when_they_came_over_a_month_ago(self):
        notes = self.notes_by_title()

        # Inception's extra copy arrived 45 days before the seed.
        self.assertNotIn('Inception', notes)

    def test_home_page__counts_several_new_copies__when_a_movie_gets_more_than_one(self):
        die_hard = Movie.objects.get(title='Die Hard')
        Copy.objects.create(movie=die_hard)

        notes = self.notes_by_title()

        self.assertTrue(notes['Die Hard'].startswith('2 new copies'))

    def test_home_page__says_nothing_is_new__when_nothing_arrived_this_month(self):
        Copy.objects.update(added_at=timezone.now() - timedelta(days=60))

        response = self.client.get('/')

        self.assertEqual(self.notes_by_title(), {})
        self.assertContains(response, 'Nothing new this month.')
