from bs4 import BeautifulSoup
from django.test import TestCase
from django.utils import timezone

from api.models import Copy, CopyReport, Rental, User


class CopyPageTestCase(TestCase):
    def setUp(self):
        self.jordans_rental = Rental.objects.select_related('copy__movie').get(
            user__username='jordan',
            returned_at__isnull=True)
        self.copy = self.jordans_rental.copy

    def get_page(self, copy: Copy):
        response = self.client.get(f'/copies/{copy.label}')
        return response, BeautifulSoup(response.content, 'html.parser')

    def test_copy_page__shows_the_movie_label_and_reports__when_the_copy_exists(self):
        CopyReport.objects.create(
            copy=self.copy,
            user=User.objects.get(username='jordan'),
            kind='scratched',
            notes='Skips at the start.')

        response, soup = self.get_page(self.copy)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(soup.title.get_text(), f'Die Hard, copy {self.copy.label} | Movie Manager')
        self.assertIsNotNone(soup.select_one(f'.copy-page__card .movie-card[data-key="{self.copy.movie_id}"]'))
        self.assertEqual(soup.select_one('#copy-page h1 code').get_text(), self.copy.label)
        rows = soup.select('.copy-page__reports .copy-report-row')
        self.assertEqual(len(rows), 1)
        self.assertIn('Scratched or skips', rows[0].get_text())
        self.assertEqual(rows[0].select_one('.copy-report-row__notes').get_text(), 'Skips at the start.')

    def test_copy_page__offers_the_report_dialog__when_the_copy_is_out_with_you(self):
        self.client.force_login(User.objects.get(username='jordan'))

        _, soup = self.get_page(self.copy)

        self.assertIsNotNone(soup.select_one('#copy-page .copy-page__report'))
        template = soup.select_one('template#report-copy-dialog-template')
        self.assertEqual(template['data-dialog-class'], 'report-copy-dialog')
        kinds = [radio['value'] for radio in template.select('input[name="kind"]')]
        self.assertEqual(kinds, ['scratched', 'broken_case', 'lost', 'other'])

    def test_copy_page__offers_no_report__when_the_copy_is_out_with_someone_else(self):
        self.client.force_login(User.objects.get(username='alex'))

        _, soup = self.get_page(self.copy)

        self.assertIsNone(soup.select_one('.copy-page__report'))
        self.assertIsNone(soup.select_one('template#report-copy-dialog-template'))
        self.assertTrue(soup.select_one('.copy-page__where').get_text().strip().startswith('Out with jordan for'))

    def test_copy_page__offers_the_report__when_staff_view_any_copy_in_rotation(self):
        self.client.force_login(User.objects.get(username='sam'))

        _, soup = self.get_page(self.copy)

        self.assertIsNotNone(soup.select_one('.copy-page__report'))

    def test_copy_page__says_out_of_rotation_without_the_report__when_retired(self):
        Copy.objects.filter(id=self.copy.id).update(retired_at=timezone.now())
        self.client.force_login(User.objects.get(username='sam'))

        _, soup = self.get_page(self.copy)

        self.assertTrue(soup.select_one('.copy-page__where').get_text().strip().startswith('Out of rotation since'))
        self.assertIsNone(soup.select_one('.copy-page__report'))

    def test_copy_page__answers_404__when_no_copy_has_the_label(self):
        response = self.client.get('/copies/zzzz-0000')

        self.assertEqual(response.status_code, 404)
        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertIn('No copy has that label', soup.get_text())

    def test_movie_page__links_each_label_to_its_copy_page__when_opened(self):
        response = self.client.get(f'/movies/{self.copy.movie_id}')

        soup = BeautifulSoup(response.content, 'html.parser')
        links = [link['href'] for link in soup.select('#movie-page .copy-table tbody td:first-child a')]
        self.assertIn(f'/copies/{self.copy.label}', links)
        self.assertEqual(len(links), 3)

    def test_movie_page__says_out_of_rotation__when_a_copy_is_retired(self):
        Copy.objects.filter(id=self.copy.id).update(retired_at=timezone.now())

        response = self.client.get(f'/movies/{self.copy.movie_id}')

        soup = BeautifulSoup(response.content, 'html.parser')
        statuses = [' '.join(cell.get_text().split()) for cell in soup.select('.copy-table tbody td:nth-of-type(3)')]
        self.assertIn('Out of rotation', statuses)

    def test_my_movies_page__links_each_label_to_its_copy_page__when_you_have_movies_out(self):
        self.client.force_login(User.objects.get(username='jordan'))

        response = self.client.get('/my-movies')

        soup = BeautifulSoup(response.content, 'html.parser')
        links = [link['href'] for link in soup.select('.rental-row .rental-row__label')]
        self.assertIn(f'/copies/{self.copy.label}', links)
