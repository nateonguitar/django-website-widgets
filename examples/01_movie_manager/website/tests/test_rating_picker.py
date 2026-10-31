from bs4 import BeautifulSoup
from django.test import TestCase

from api.admin.movie_admin import MovieAdminForm
from api.models import Movie, MovieRating
from website.widgets.rating_picker import RatingPicker


class RatingPickerTestCase(TestCase):
    def test_rating_picker__carries_each_ratings_description__when_rendered(self):
        soup = BeautifulSoup(RatingPicker(name='rating').render(), 'html.parser')

        descriptions = {
            option['value']: option['data-description']
            for option in soup.select('select[name="rating"] option')
        }
        self.assertEqual(descriptions[''], '')
        self.assertEqual(descriptions['PG13'], MovieRating.PG13.description)
        self.assertEqual(soup.select_one('.rating-picker__description').get_text(), '')

    def test_rating_picker__shows_the_chosen_ratings_description__when_rendered_with_a_value(self):
        soup = BeautifulSoup(RatingPicker(name='rating', value='R').render(), 'html.parser')

        self.assertEqual(soup.select_one('option[selected]')['value'], 'R')
        self.assertEqual(soup.select_one('.rating-picker__description').get_text(), MovieRating.R.description)

    def test_rating_picker__starts_its_controller_on_its_own_root__when_rendered_for_a_field(self):
        html = RatingPicker(name='rating', select_id='id_rating').render()

        soup = BeautifulSoup(html, 'html.parser')
        self.assertIsNotNone(soup.select_one('#rating-picker-id_rating select#id_rating'))
        self.assertIn(
            "await App.initController(new RatingPickerController(), '#rating-picker-id_rating');",
            soup.select_one('script[type="module"]').get_text())


class RatingSelectTestCase(TestCase):
    """RatingPicker inside a Django form, as the Movie admin uses it."""

    def test_rating_select__renders_the_picker_with_the_fields_id__when_in_a_form(self):
        form = MovieAdminForm(instance=Movie.objects.get(title='Die Hard'))

        soup = BeautifulSoup(str(form['rating']), 'html.parser')

        select = soup.select_one('.rating-picker select')
        self.assertEqual(select['name'], 'rating')
        self.assertEqual(select['id'], 'id_rating')
        self.assertEqual(select.select_one('option[selected]')['value'], 'R')

    def test_rating_select__saves_the_chosen_rating__when_the_form_is_submitted(self):
        die_hard = Movie.objects.get(title='Die Hard')
        data = {'title': die_hard.title, 'year': die_hard.year, 'genre': die_hard.genre, 'rating': 'PG13'}

        form = MovieAdminForm(data=data, instance=die_hard)

        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        die_hard.refresh_from_db()
        self.assertEqual(die_hard.rating, 'PG13')
