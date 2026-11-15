from api.models import Copy, Genre, Movie, MovieRating, Rental, User
from website.tests.playwright_test_case import PlaywrightTestCase


class CheckoutBrowserTestCase(PlaywrightTestCase):
    """A flow over two pages: the browser's requests and the test's assertions share one database."""

    @classmethod
    def setUpTestData(cls):
        cls.alex = User.objects.get(username='alex')
        cls.jordan = User.objects.get(username='jordan')
        cls.up = Movie.objects.create(title='Up', year=2009, genre=Genre.ANIMATION, rating=MovieRating.PG)
        cls.coco = Movie.objects.create(title='Coco', year=2017, genre=Genre.ANIMATION, rating=MovieRating.PG)
        Copy.objects.create_copies(cls.up, 1)
        Copy.objects.create_copies(cls.coco, 1)

    def add_to_cart(self, movie: Movie):
        movie_card = self.page.locator(f'.movie-card[data-movie-id="{movie.id}"]')
        cart_button = movie_card.locator('.movie-card__action')
        cart_button.click()
        # click() returns once the click lands; the card's controller relabels the button after.
        remove_from_cart_button = movie_card.get_by_text('Remove from cart')
        remove_from_cart_button.wait_for()

    def test_checkout__records_a_rental__when_the_cart_is_taken(self):
        self.login(self.alex)
        self.goto('/find?q=Up')
        self.add_to_cart(self.up)

        self.goto('/cart')
        checkout_button = self.page.locator('.cart-page__checkout-button')
        checkout_button.click()

        # In the page from the start, hidden: visible once the checkout request succeeded.
        done_message = self.page.locator('.cart-page__done')
        done_message.wait_for()
        open_rentals = Rental.objects.filter(user=self.alex, copy__movie=self.up, returned_at__isnull=True)
        self.assertTrue(open_rentals.exists())

    def test_checkout__offers_the_rest__when_a_movie_ran_out(self):
        self.login(self.alex)
        self.goto('/find?genre=animation')
        self.add_to_cart(self.up)
        self.add_to_cart(self.coco)
        # Someone else takes the only Up while it sits in the cart.
        only_up = Copy.objects.get(movie=self.up)
        Rental.objects.create(copy=only_up, user=self.jordan)

        self.goto('/cart')
        checkout_button = self.page.locator('.cart-page__checkout-button')
        checkout_button.click()
        confirm_dialog = self.page.locator('dialog.confirm-dialog')
        confirm_text = confirm_dialog.locator('.confirm-dialog__message').inner_text()
        self.assertIn('Up ran out', confirm_text)
        yes_button = confirm_dialog.locator('.confirm-dialog__yes')
        yes_button.click()

        done_message = self.page.locator('.cart-page__done')
        done_message.wait_for()
        coco_rentals = Rental.objects.filter(user=self.alex, copy__movie=self.coco)
        up_rentals = Rental.objects.filter(user=self.alex, copy__movie=self.up)
        self.assertTrue(coco_rentals.exists())
        self.assertFalse(up_rentals.exists())
