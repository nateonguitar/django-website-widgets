import json

from django.db import IntegrityError, transaction
from django.test import TestCase

from api.models import Copy, Movie, Rental, User


class CheckoutTestCase(TestCase):
    def setUp(self):
        self.alex = User.objects.get(username='alex')
        self.client.force_login(self.alex)

    def checkout(self, movie_ids: list[int]):
        return self.client.post(
            '/api/rentals/checkout',
            data=json.dumps({'movie_ids': movie_ids}),
            content_type='application/json')

    def movie(self, title: str) -> Movie:
        return Movie.objects.get(title=title)

    def test_checkout__succeeds_recording_a_copy_of_each__when_all_are_available(self):
        die_hard = self.movie('Die Hard')
        toy_story = self.movie('Toy Story')

        response = self.checkout([die_hard.id, toy_story.id])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['rental_ids']), 2)
        open_rentals = Rental.objects.filter(user=self.alex, returned_at__isnull=True)
        self.assertEqual(
            sorted(rental.copy.movie.title for rental in open_rentals),
            ['Die Hard', 'Toy Story'])

    def test_checkout__takes_a_copy_nobody_has__when_one_is_already_out(self):
        die_hard = self.movie('Die Hard')
        jordans_copy = Rental.objects.get(user__username='jordan', copy__movie=die_hard, returned_at__isnull=True).copy

        self.checkout([die_hard.id])

        alexs_rental = Rental.objects.get(user=self.alex, returned_at__isnull=True)
        self.assertNotEqual(alexs_rental.copy_id, jordans_copy.id)

    def test_checkout__fails_recording_nothing__when_a_movie_has_no_copy_left(self):
        spirited_away = self.movie('Spirited Away')
        toy_story = self.movie('Toy Story')

        response = self.checkout([toy_story.id, spirited_away.id])

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['unavailable_movie_ids'], [spirited_away.id])
        self.assertFalse(Rental.objects.filter(user=self.alex, returned_at__isnull=True).exists())

    def test_checkout__fails__when_cart_is_empty(self):
        response = self.checkout([])

        self.assertEqual(response.status_code, 400)

    def test_checkout__fails__when_signed_out(self):
        self.client.logout()

        response = self.checkout([self.movie('Toy Story').id])

        self.assertEqual(response.status_code, 401)

    def test_one_open_rental_per_copy__refuses_a_second__when_copy_is_already_out(self):
        # What stops two checkouts racing for the last copy: whichever inserts second fails.
        copy = Copy.objects.get(movie__title='Spirited Away')

        with self.assertRaises(IntegrityError), transaction.atomic():
            Rental.objects.create(copy=copy, user=self.alex)
