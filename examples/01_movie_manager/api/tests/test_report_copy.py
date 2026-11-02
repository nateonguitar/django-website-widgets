from django.core import mail
from django.test import TestCase

from api.models import Copy, Movie, Rental, User


class ReportCopyTestCase(TestCase):
    def setUp(self):
        self.jordans_rental = Rental.objects.select_related('copy').get(user__username='jordan', returned_at__isnull=True)
        self.copy = self.jordans_rental.copy

    def report(self, label: str, **body):
        payload = {'kind': 'scratched', 'notes': 'Skips at the start of chapter 3.', **body}
        return self.client.post(f'/api/copies/{label}/reports', payload, content_type='application/json')

    def test_report_copy__succeeds_keeping_it_in_rotation__when_it_is_out_with_you(self):
        self.client.force_login(User.objects.get(username='jordan'))

        response = self.report(self.copy.label)

        self.assertEqual(response.status_code, 201)
        report = self.copy.reports.get()
        self.assertEqual(response.json(), {'report_id': report.id, 'label': self.copy.label, 'retired': False})
        self.assertEqual((report.copy, report.user.username, report.kind), (self.copy, 'jordan', 'scratched'))
        self.copy.refresh_from_db()
        self.assertIsNone(self.copy.retired_at)
        self.jordans_rental.refresh_from_db()
        self.assertIsNone(self.jordans_rental.returned_at)

    def test_report_copy__retires_it_and_closes_the_rental__when_unrecoverable(self):
        self.client.force_login(User.objects.get(username='jordan'))
        before = Movie.objects.with_availability().get(id=self.copy.movie_id)

        response = self.report(self.copy.label, kind='lost', unrecoverable=True)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['retired'])
        self.copy.refresh_from_db()
        self.assertIsNotNone(self.copy.retired_at)
        self.jordans_rental.refresh_from_db()
        self.assertIsNotNone(self.jordans_rental.returned_at)
        # A lost disc isn't "back on the shelf", so no return receipt.
        self.assertEqual(mail.outbox, [])
        after = Movie.objects.with_availability().get(id=self.copy.movie_id)
        self.assertEqual(after.total_copies, before.total_copies - 1)
        self.assertEqual(after.available_copies, before.available_copies)

    def test_report_copy__fails_with_field_errors__when_the_form_is_incomplete(self):
        self.client.force_login(User.objects.get(username='jordan'))

        response = self.report(self.copy.label, kind='melted', notes='   ')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {'errors': {'kind': "Pick what's wrong with it.", 'notes': 'Say a little about it.'}})
        self.assertFalse(self.copy.reports.exists())

    def test_report_copy__fails_with_a_field_error__when_the_notes_are_too_long(self):
        self.client.force_login(User.objects.get(username='jordan'))

        response = self.report(self.copy.label, notes='x' * 1001)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'errors': {'notes': 'At most 1000 characters.'}})

    def test_report_copy__fails__when_the_copy_is_out_with_someone_else(self):
        self.client.force_login(User.objects.get(username='alex'))

        response = self.report(self.copy.label)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'message': "That copy isn't out with you."})
        self.assertFalse(self.copy.reports.exists())

    def test_report_copy__fails__when_the_label_is_unknown(self):
        self.client.force_login(User.objects.get(username='jordan'))

        response = self.report('zzzz-0000')

        self.assertEqual(response.status_code, 404)

    def test_report_copy__succeeds__when_staff_report_a_copy_on_the_shelf(self):
        self.client.force_login(User.objects.get(username='sam'))
        # On the shelf, with no seeded reports.
        on_the_shelf = Copy.objects.filter(movie__title='Toy Story').first()

        response = self.report(on_the_shelf.label, kind='broken_case')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(on_the_shelf.reports.get().user.username, 'sam')

    def test_report_copy__fails__when_the_copy_is_already_retired(self):
        self.client.force_login(User.objects.get(username='sam'))
        Copy.objects.filter(id=self.copy.id).update(retired_at=self.jordans_rental.taken_at)

        response = self.report(self.copy.label)

        self.assertEqual(response.status_code, 404)

    def test_report_copy__fails__when_signed_out(self):
        response = self.report(self.copy.label)

        self.assertEqual(response.status_code, 401)
