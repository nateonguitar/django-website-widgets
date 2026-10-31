from bs4 import BeautifulSoup
from django.test import TestCase

from api.models import Copy, Movie, Rental, User


class AdminTestCase(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.get(username='sam'))

    def test_admin__lists_every_model__when_signed_in_as_staff(self):
        # A column or filter naming something that doesn't exist only fails when the page renders.
        for path in ['/admin/api/movie/', '/admin/api/copy/', '/admin/api/rental/', '/admin/api/user/']:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_admin__opens_a_movie_with_its_copies__when_one_is_chosen(self):
        die_hard = Movie.objects.get(title='Die Hard')

        response = self.client.get(f'/admin/api/movie/{die_hard.id}/change/')

        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertEqual(len(soup.select('#copies-group tbody tr.has_original')), 3)

    def test_admin__picks_the_rating_with_the_sites_rating_picker__when_a_movie_is_opened(self):
        die_hard = Movie.objects.get(title='Die Hard')

        response = self.client.get(f'/admin/api/movie/{die_hard.id}/change/')

        soup = BeautifulSoup(response.content, 'html.parser')
        picker = soup.select_one('.field-rating .rating-picker')
        self.assertEqual(picker.select_one('option[selected]')['value'], 'R')
        self.assertTrue(picker.select_one('.rating-picker__description').get_text().startswith('Restricted'))

    def test_admin__offers_a_return_button__when_a_rental_is_still_out(self):
        open_rental = Rental.objects.get(copy__movie__title='Die Hard', returned_at__isnull=True)

        response = self.client.get(f'/admin/api/rental/{open_rental.id}/change/')

        soup = BeautifulSoup(response.content, 'html.parser')
        field = soup.select_one('.field-returned .return-rental-field')
        self.assertEqual(field['data-url'], f'/api/rentals/{open_rental.id}/return')
        self.assertEqual(field.select_one('button')['type'], 'button')
        # How long, from the site's own Timestamp widget nested in this admin one.
        self.assertTrue(' '.join(field.get_text().split()).startswith('Out with jordan for 4'))
        self.assertIsNotNone(field.select_one('time[datetime]'))
        # Shown by the widget, never an input the form could save back.
        self.assertIsNone(soup.select_one('[name="returned_at"]'))

    def test_admin__shows_when_it_came_back__when_a_rental_is_returned(self):
        returned = Rental.objects.filter(returned_at__isnull=False).first()

        response = self.client.get(f'/admin/api/rental/{returned.id}/change/')

        soup = BeautifulSoup(response.content, 'html.parser')
        field = soup.select_one('.field-returned')
        self.assertIsNone(field.select_one('button'))
        self.assertIsNone(field.select_one('.return-rental-field'))
        self.assertTrue(field.select_one('time').get_text().endswith(' ago'))

    def test_admin__shows_the_movie_pages_copy_table__when_a_movie_is_opened(self):
        die_hard = Movie.objects.get(title='Die Hard')

        response = self.client.get(f'/admin/api/movie/{die_hard.id}/change/')

        soup = BeautifulSoup(response.content, 'html.parser')
        # The CopyTable widget, rendered with render() into a read-only field.
        field = soup.select_one('.field-where_each_copy_is')
        statuses = [' '.join(cell.get_text().split()) for cell in field.select('table.copy-table tbody td:nth-of-type(3)')]
        self.assertEqual(statuses.count('On the shelf'), 2)
        # Staff see who has the other: jordan, from the seed.
        self.assertEqual(len([status for status in statuses if status.startswith('Out with jordan for ')]), 1)

    def test_admin__shows_only_open_rentals__when_filtered_to_still_out(self):
        response = self.client.get('/admin/api/rental/', {'status': 'out'})

        soup = BeautifulSoup(response.content, 'html.parser')
        # The first column is the row's link, so a <th>.
        movies = sorted(cell.get_text(strip=True) for cell in soup.select('#result_list .field-movie'))
        # The seed's two open rentals.
        self.assertEqual(movies, ['Die Hard', 'Spirited Away'])

    def test_admin__marks_only_open_rentals_returned__when_the_action_runs(self):
        open_rental = Rental.objects.get(copy__movie__title='Die Hard', returned_at__isnull=True)
        old_rental = Rental.objects.filter(returned_at__isnull=False).first()
        old_returned_at = old_rental.returned_at

        self.client.post('/admin/api/rental/', {
            'action': 'mark_returned',
            '_selected_action': [open_rental.id, old_rental.id],
        })

        open_rental.refresh_from_db()
        old_rental.refresh_from_db()
        self.assertIsNotNone(open_rental.returned_at)
        self.assertEqual(old_rental.returned_at, old_returned_at)

    def test_admin__lists_only_copies_someone_has__when_filtered_to_not_on_the_shelf(self):
        response = self.client.get('/admin/api/copy/', {'on_the_shelf': 'no'})

        soup = BeautifulSoup(response.content, 'html.parser')
        movies = sorted(cell.get_text(strip=True) for cell in soup.select('#result_list td.field-movie'))
        # The seed's two open rentals.
        self.assertEqual(movies, ['Die Hard (1988)', 'Spirited Away (2001)'])

    def test_admin__leaves_out_copies_someone_has__when_filtered_to_on_the_shelf(self):
        response = self.client.get('/admin/api/copy/', {'on_the_shelf': 'yes'})

        soup = BeautifulSoup(response.content, 'html.parser')
        movies = [cell.get_text(strip=True) for cell in soup.select('#result_list td.field-movie')]
        self.assertNotIn('Spirited Away (2001)', movies)
        self.assertEqual(len(movies), Copy.objects.count() - 2)

    def test_admin__marks_a_copy_off_the_shelf__when_it_is_out(self):
        response = self.client.get('/admin/api/copy/', {'q': 'Spirited Away'})

        soup = BeautifulSoup(response.content, 'html.parser')
        icon = soup.select_one('#result_list td.field-on_the_shelf img')
        self.assertEqual(icon['alt'], 'False')
        self.assertEqual(Copy.objects.filter(movie__title='Spirited Away').count(), 1)
