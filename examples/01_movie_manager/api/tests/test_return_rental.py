from django.test import TestCase

from api.models import Rental, User


class ReturnRentalTestCase(TestCase):
    def setUp(self):
        self.jordans_rental = Rental.objects.get(user__username='jordan', returned_at__isnull=True)

    def return_rental(self, rental: Rental):
        return self.client.post(f'/api/rentals/{rental.id}/return')

    def test_return_rental__succeeds_closing_it__when_it_is_out_with_you(self):
        self.client.force_login(User.objects.get(username='jordan'))

        response = self.return_rental(self.jordans_rental)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'title': 'Die Hard'})
        self.jordans_rental.refresh_from_db()
        self.assertIsNotNone(self.jordans_rental.returned_at)

    def test_return_rental__fails__when_it_is_someone_elses(self):
        self.client.force_login(User.objects.get(username='alex'))

        response = self.return_rental(self.jordans_rental)

        self.assertEqual(response.status_code, 404)
        self.jordans_rental.refresh_from_db()
        self.assertIsNone(self.jordans_rental.returned_at)

    def test_return_rental__fails__when_already_returned(self):
        self.client.force_login(User.objects.get(username='jordan'))
        self.return_rental(self.jordans_rental)

        response = self.return_rental(self.jordans_rental)

        self.assertEqual(response.status_code, 404)

    def test_return_rental__fails__when_signed_out(self):
        response = self.return_rental(self.jordans_rental)

        self.assertEqual(response.status_code, 401)
