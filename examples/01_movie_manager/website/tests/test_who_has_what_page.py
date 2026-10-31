from datetime import timedelta

from bs4 import BeautifulSoup
from django.test import TestCase
from django.utils import timezone

from api.models import Copy, Rental, User


class WhoHasWhatPageTestCase(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.get(username='alex'))

    def table_rows(self) -> list[list[str]]:
        """Each row of the table, as its cells' text: the movie, who has it and for how long."""
        soup = BeautifulSoup(self.client.get('/who-has-what').content, 'html.parser')
        rows = soup.select('.who-has-what-page__table tbody tr')
        return [[cell.get_text(strip=True) for cell in row.select('td')] for row in rows]

    def test_who_has_what_page__shows_who_has_each_movie_and_for_how_long__when_movies_are_out(self):
        toy_story = Copy.objects.filter(movie__title='Toy Story').first()
        rental = Rental.objects.create(copy=toy_story, user=User.objects.get(username='sam'))
        # taken_at is auto_now_add, so it's backdated after the insert.
        Rental.objects.filter(id=rental.id).update(taken_at=timezone.now() - timedelta(weeks=3))

        rows = self.table_rows()

        self.assertIn(['Toy Story', 'sam', '3\xa0weeks'], rows)
        # The seeded rentals are still there.
        self.assertEqual(len(rows), 3)

    def test_who_has_what_page__shows_how_long_the_seeded_rentals_have_been_out__when_opened(self):
        rows = self.table_rows()

        self.assertCountEqual(
            rows,
            [
                ['Die Hard', 'jordan', '4\xa0days'],
                ['Spirited Away', 'sam', '3\xa0weeks, 2\xa0days'],
            ])

    def test_who_has_what_page__says_you__when_you_have_it(self):
        Rental.objects.create(copy=Copy.objects.filter(movie__title='Toy Story').first(), user=User.objects.get(username='alex'))

        rows = self.table_rows()

        self.assertIn(['Toy Story', 'You', 'less than a minute'], rows)

    def test_who_has_what_page__leaves_out_returned_movies__when_one_was_brought_back(self):
        Rental.objects.update(returned_at=timezone.now())

        response = self.client.get('/who-has-what')

        self.assertEqual(self.table_rows(), [])
        self.assertContains(response, 'Everything is on the shelf.')

    def test_who_has_what_page__answers_401__when_signed_out(self):
        self.client.logout()

        response = self.client.get('/who-has-what')

        self.assertEqual(response.status_code, 401)
