import json

from django.test import TestCase

from api.models import Movie, User


class CreateMovieTestCase(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.get(username='sam'))

    def create_movie(self, **payload):
        return self.client.post('/api/movies', data=json.dumps(payload), content_type='application/json')

    def test_create_movie__succeeds_with_its_copies__when_every_field_is_valid(self):
        response = self.create_movie(title='Moana', year=2016, genre='animation', rating='PG', copies=2)

        self.assertEqual(response.status_code, 201)
        movie = Movie.objects.get(title='Moana')
        self.assertEqual(movie.copies.count(), 2)

    def test_create_movie__fails_with_each_field_error__when_fields_are_missing(self):
        response = self.create_movie(title=' ', year=None, genre='', rating='X', copies=0)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            sorted(response.json()['errors']),
            ['copies', 'genre', 'rating', 'title', 'year'])

    def test_create_movie__fails_pointing_at_copies__when_movie_is_already_here(self):
        response = self.create_movie(title='die hard', year=1988, genre='action', rating='R', copies=1)

        self.assertEqual(response.status_code, 400)
        self.assertIn('copy', response.json()['errors']['title'])
        self.assertEqual(Movie.objects.filter(title__iexact='die hard').count(), 1)

    def test_create_movie__fails__when_signed_out(self):
        self.client.logout()

        response = self.create_movie(title='Moana', year=2016, genre='animation', rating='PG', copies=1)

        self.assertEqual(response.status_code, 401)
