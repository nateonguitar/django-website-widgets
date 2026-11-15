from api.models import User
from website.tests.playwright_test_case import PlaywrightTestCase


class SignInBrowserTestCase(PlaywrightTestCase):
    def test_sign_in__lands_on_next_signed_in__when_the_form_is_sent(self):
        self.goto('/sign-in?next=/my-movies')
        username_input = self.page.locator('.sign-in-page__username')
        password_input = self.page.locator('.sign-in-page__password')
        submit_button = self.page.locator('.sign-in-page__submit-button')
        username_input.fill('alex')
        password_input.fill('try-the-widgets')
        submit_button.click()

        # The session cookie the endpoint set came back with the next page's request.
        self.page.wait_for_url('**/my-movies')
        signed_in_as = self.page.locator('#account-menu .account-menu__button').inner_text()
        self.assertEqual(signed_in_as, 'alex')

    def test_sign_in__redirects_home__when_already_signed_in(self):
        alex = User.objects.get(username='alex')
        self.login(alex)

        # A server-side redirect, which the recipe follows for the browser.
        self.goto('/sign-in')

        home_url = f'{self.HOST}/'
        self.assertEqual(self.page.url, home_url)
