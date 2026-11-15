from bs4 import BeautifulSoup
from django.urls import reverse

from api.models import Copy, Genre, Movie, MovieRating, Rental, User
from website.tests.app_widget_test_case import AppWidgetTestCase
from website.widgets.movie_card import MovieCard


class MovieCardTestCase(AppWidgetTestCase):
    """
    Beside its widget, since it tests this one widget: each permutation a card can be in,
    without finding a page that happens to show it.
    """

    @classmethod
    def setUpTestData(cls):
        cls.alex = User.objects.get(username='alex')
        movie = Movie.objects.create(title='Paddington', year=2014, genre=Genre.FAMILY, rating=MovieRating.PG)
        copies = Copy.objects.create_copies(movie, 2)
        Rental.objects.create(copy=copies[0], user=cls.alex)
        cls.movie_id = movie.id

    async def render_movie_card(self, user=None, purpose: str = 'cart') -> BeautifulSoup:
        # From with_availability(), as every caller passes it, for the copy counts.
        movies = Movie.objects.with_availability()
        movie = await movies.aget(id=self.movie_id)
        movie_card = MovieCard(movie=movie, purpose=purpose, key=movie.id)
        html = await self.arender_document(movie_card, user=user)
        return BeautifulSoup(html, 'html.parser')

    async def test_movie_card__links_to_sign_in_and_back__when_signed_out(self):
        soup = await self.render_movie_card()

        sign_in_link = soup.select_one('.movie-card .movie-card__sign-in')
        cart_button = soup.select_one('.movie-card__action')
        sign_in_url = reverse('website:SignInPage')
        movie_url = reverse('website:MoviePage', args=[self.movie_id])
        expected_href = f'{sign_in_url}?next={movie_url}'
        self.assertEqual(sign_in_link['href'], expected_href)
        self.assertIsNone(cart_button)

    async def test_movie_card__has_the_cart_button__when_signed_in(self):
        soup = await self.render_movie_card(user=self.alex)

        movie_card = soup.select_one('.movie-card')
        cart_button = movie_card.select_one('button.movie-card__action')
        sign_in_link = movie_card.select_one('.movie-card__sign-in')
        availability_text = movie_card.select_one('.movie-card__availability').get_text(strip=True)
        self.assertIsNotNone(cart_button)
        self.assertIsNone(sign_in_link)
        self.assertEqual(movie_card['data-available'], '1')
        self.assertEqual(availability_text, '1 of 2 available')

    async def test_movie_card__has_the_choose_button__when_purpose_is_choose_and_signed_out(self):
        soup = await self.render_movie_card(purpose='choose')

        movie_card = soup.select_one('.movie-card')
        choose_button = movie_card.select_one('button.movie-card__action')
        self.assertEqual(movie_card['data-purpose'], 'choose')
        self.assertIsNotNone(choose_button)

    async def test_movie_card__starts_its_controller_beside_the_appbar__when_rendered(self):
        soup = await self.render_movie_card(user=self.alex)

        # The card's controller tells the appbar's cart count when the cart changes, so the
        # document holds the appbar as a page would.
        cart_count_badge = soup.select_one('#appbar .appbar__cart-count')
        scripts = [
            script.get_text()
            for script in soup.select('script[type="module"]')
        ]
        all_scripts = '\n'.join(scripts)
        movie_card_selector = f'.movie-card[data-key="{self.movie_id}"]'
        expected_start = f"await App.initController(new MovieCardController(), '{movie_card_selector}');"
        self.assertIsNotNone(cart_count_badge)
        self.assertIn(expected_start, all_scripts)
