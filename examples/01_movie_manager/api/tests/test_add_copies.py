import json

from django.test import TestCase

from api.models import Movie, User


class AddCopiesTestCase(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.get(username='sam'))
        self.die_hard = Movie.objects.get(title='Die Hard')

    def add_copies(self, movie_id: int, copies: int):
        return self.client.post(
            f'/api/movies/{movie_id}/copies',
            data=json.dumps({'copies': copies}),
            content_type='application/json')

    def test_add_copies__succeeds_returning_the_total__when_movie_exists(self):
        response = self.add_copies(self.die_hard.id, 2)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {'title': 'Die Hard', 'total_copies': 5})

    def test_add_copies__fails__when_count_is_out_of_range(self):
        response = self.add_copies(self.die_hard.id, 0)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.die_hard.copies.count(), 3)

    def test_add_copies__fails__when_movie_does_not_exist(self):
        response = self.add_copies(999_999, 1)

        self.assertEqual(response.status_code, 404)

    def test_add_copies__fails__when_signed_out(self):
        self.client.logout()

        response = self.add_copies(self.die_hard.id, 1)

        self.assertEqual(response.status_code, 401)
