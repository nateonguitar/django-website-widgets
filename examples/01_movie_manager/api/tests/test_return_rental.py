from bs4 import BeautifulSoup
from django.core import mail
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

    def test_return_rental__emails_a_receipt_with_the_shared_footer__when_it_succeeds(self):
        self.client.force_login(User.objects.get(username='jordan'))

        self.return_rental(self.jordans_rental)

        self.assertEqual(len(mail.outbox), 1)
        receipt = mail.outbox[0]
        self.assertEqual(receipt.to, ['jordan@example.com'])
        self.assertEqual(receipt.subject, 'Die Hard is back on the shelf')
        html, _ = receipt.alternatives[0]
        soup = BeautifulSoup(html, 'html.parser')
        self.assertIn('Die Hard (1988) is back on the shelf', ' '.join(soup.body.get_text().split()))
        # The EmailFooter every email ends with.
        footer_links = [link['href'] for link in soup.select('body > div:last-child a')]
        self.assertEqual(
            footer_links,
            ['http://localhost:8000', 'http://localhost:8000/my-movies', 'http://localhost:8000/who-has-what'])

    def test_return_rental__succeeds_emailing_whoever_had_it__when_staff_return_someone_elses(self):
        # sam is staff, returning jordan's copy from the Rental admin.
        self.client.force_login(User.objects.get(username='sam'))

        response = self.return_rental(self.jordans_rental)

        self.assertEqual(response.status_code, 200)
        self.jordans_rental.refresh_from_db()
        self.assertIsNotNone(self.jordans_rental.returned_at)
        self.assertEqual(mail.outbox[0].to, ['jordan@example.com'])

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
