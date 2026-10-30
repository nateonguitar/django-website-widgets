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
