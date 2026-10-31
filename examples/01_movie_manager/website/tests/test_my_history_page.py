import json
from datetime import timedelta

from bs4 import BeautifulSoup
from django.test import TestCase
from django.utils import timezone

from api.models import Copy, Rental, User


class MyHistoryPageTestCase(TestCase):
    def setUp(self):
        self.alex = User.objects.get(username='alex')
        self.client.force_login(self.alex)

    def history_rows(self) -> list[list[str]]:
        """Each row of the table, as its cells' text."""
        soup = BeautifulSoup(self.client.get('/my-history').content, 'html.parser')
        rows = soup.select('.my-history-page__table tbody tr')
        return [[cell.get_text(' ', strip=True) for cell in row.select('td')] for row in rows]

    def test_my_history_page__lists_your_rentals_newest_first__when_signed_in(self):
        newest = Rental.objects.filter(user=self.alex).order_by('-taken_at').first()
        oldest = Rental.objects.filter(user=self.alex).order_by('taken_at').first()

        rows = self.history_rows()

        taken_column = 1
        self.assertEqual(rows[0][taken_column], newest.taken_at.strftime('%a %-d %b %Y'))
        self.assertEqual(rows[-1][taken_column], oldest.taken_at.strftime('%a %-d %b %Y'))

    def test_my_history_page__leaves_out_other_peoples_rentals__when_signed_in(self):
        Rental.objects.filter(user=self.alex).delete()
        Rental.objects.create(copy=Copy.objects.filter(movie__title='Toy Story').first(), user=self.alex)

        rows = self.history_rows()

        # Not jordan's open Die Hard.
        self.assertEqual([row[0] for row in rows], ['Toy Story'])

    def test_my_history_page__shows_a_movie_you_still_have__when_one_is_out(self):
        self.client.force_login(User.objects.get(username='jordan'))

        response = self.client.get('/my-history')

        soup = BeautifulSoup(response.content, 'html.parser')
        still_out = soup.select('.my-history-page__table tr.history-row--out')
        self.assertEqual(len(still_out), 1)
        self.assertEqual(still_out[0].select_one('td').get_text(strip=True), 'Die Hard')
        self.assertEqual(still_out[0].select_one('a').get_text(strip=True), 'return it')

    def test_my_history_page__charts_each_of_the_last_90_days__when_signed_in(self):
        Rental.objects.filter(user=self.alex).delete()
        toy_story = Copy.objects.filter(movie__title='Toy Story').first()
        Rental.objects.create(copy=toy_story, user=self.alex, returned_at=timezone.now())
        three_days_ago = Rental.objects.create(copy=toy_story, user=self.alex, returned_at=timezone.now())
        Rental.objects.filter(id=three_days_ago.id).update(taken_at=timezone.now() - timedelta(days=3))

        response = self.client.get('/my-history')

        soup = BeautifulSoup(response.content, 'html.parser')
        page = soup.select_one('#my-history-page')
        # The same JSON the controller parses from its root's dataset.
        labels = json.loads(page['data-chart-labels'])
        counts = json.loads(page['data-chart-counts'])
        self.assertEqual(len(labels), 90)
        self.assertEqual(counts[-1], 1)
        self.assertEqual(counts[-4], 1)
        self.assertEqual(sum(counts), 2)
        total = soup.select_one('.my-history-page__chart-total').get_text(' ', strip=True)
        self.assertEqual(total, '2 in the last 90 days')

    def test_my_history_page__says_nothing_taken__when_you_have_no_rentals(self):
        Rental.objects.filter(user=self.alex).delete()

        response = self.client.get('/my-history')

        self.assertEqual(self.history_rows(), [])
        self.assertContains(response, "You haven't taken any movies yet.")
