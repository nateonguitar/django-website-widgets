import unittest

try:
    import playwright  # noqa: F401
except ImportError:
    # Django imports a test module before it applies --exclude-tag, so a guard here, not a tag,
    # keeps a run without Playwright installed (CI's) passing. Unittest reports it as one skip.
    raise unittest.SkipTest('Playwright is not installed; see the README to run the browser tests')

from api.models import Copy, Genre, Movie, MovieRating, User
from website.tests.playwright_test_case import PlaywrightTestCase
from website.widgets.movie_card import MovieCard


class MovieCardBrowserTestCase(PlaywrightTestCase):
    """The card alone in a browser, its controller running against the appbar a page would have."""

    @classmethod
    def setUpTestData(cls):
        cls.alex = User.objects.get(username='alex')
        cls.paddington = Movie.objects.create(title='Paddington', year=2014, genre=Genre.FAMILY, rating=MovieRating.PG)
        Copy.objects.create_copies(cls.paddington, 1)
        cls.no_copies = Movie.objects.create(title='Paddington 2', year=2017, genre=Genre.FAMILY, rating=MovieRating.PG)

    def build_movie_card(self, movie: Movie) -> MovieCard:
        movies = Movie.objects.with_availability()
        movie = movies.get(id=movie.id)
        return MovieCard(movie=movie, key=movie.id)

    def test_movie_card__counts_in_the_appbar__when_added_to_the_cart(self):
        movie_card = self.build_movie_card(self.paddington)
        self.open_widget(movie_card, user=self.alex)
        cart_button = self.page.locator('.movie-card__action')
        label_before = cart_button.inner_text()
        self.assertEqual(label_before, 'Add to cart')

        cart_button.click()

        label_after = cart_button.inner_text()
        cart_count = self.page.locator('.appbar__cart-count').inner_text()
        self.assertEqual(label_after, 'Remove from cart')
        self.assertEqual(cart_count, '1')

    def test_movie_card__disables_its_button__when_no_copy_is_available(self):
        movie_card = self.build_movie_card(self.no_copies)

        self.open_widget(movie_card, user=self.alex)

        cart_button = self.page.locator('.movie-card__action')
        label = cart_button.inner_text()
        disabled = cart_button.is_disabled()
        self.assertEqual(label, 'None available')
        self.assertTrue(disabled)
