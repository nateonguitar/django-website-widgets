from bs4 import BeautifulSoup
from django.test import TestCase

from api.models import User


class AppPageTestCase(TestCase):
    """What every page gets from AppPage and the document template, checked on the home page."""

    def test_app_page__hands_the_frontend_its_urls__when_rendered(self):
        response = self.client.get('/')

        self.assertContains(response, "AppUrls.endpoint_search_movies = '/api/movies/search';")
        self.assertContains(
            response,
            "AppUrls.endpoint_return_rental = '/api/rentals/{rental_id}/return';")

    def test_app_page__sets_the_user_on_app_state__when_signed_in(self):
        alex = User.objects.get(username='alex')
        self.client.force_login(alex)

        response = self.client.get('/')

        self.assertContains(response, f'id: {alex.id},')
        self.assertContains(response, "username: 'alex',")
        self.assertContains(response, 'AppState.csrfToken = ')

    def test_app_page__leaves_the_user_off_app_state__when_signed_out(self):
        response = self.client.get('/')

        self.assertNotContains(response, 'AppState.user =')
        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertIsNotNone(soup.select_one('.appbar__links a[href="/sign-in?next=/"]'))
        self.assertIsNone(soup.select_one('.account-menu__dialog'))

    def test_app_page__arrives_in_the_chosen_theme__when_theme_cookie_is_set(self):
        self.client.cookies['movie_manager_theme'] = 'dark'

        response = self.client.get('/')

        soup = BeautifulSoup(response.content, 'html.parser')
        self.assertEqual(soup.html['data-theme'], 'dark')

    def test_app_page__follows_the_system_theme__when_theme_cookie_is_missing_or_unknown(self):
        for cookie in (None, 'neon'):
            with self.subTest(cookie=cookie):
                if cookie:
                    self.client.cookies['movie_manager_theme'] = cookie

                response = self.client.get('/')

                soup = BeautifulSoup(response.content, 'html.parser')
                self.assertEqual(soup.html['data-theme'], 'system')

    def test_app_page__carries_the_confirm_dialog_template__when_rendered(self):
        response = self.client.get('/')

        soup = BeautifulSoup(response.content, 'html.parser')
        template = soup.select_one('template#confirm-dialog-template')
        buttons = [button['class'][0] for button in template.select('button')]
        self.assertEqual(template['data-dialog-class'], 'confirm-dialog')
        self.assertEqual(buttons, ['confirm-dialog__no', 'confirm-dialog__yes'])

    def test_app_page__puts_theme_and_sign_out_in_the_account_dialog__when_signed_in(self):
        self.client.force_login(User.objects.get(username='alex'))

        response = self.client.get('/')

        soup = BeautifulSoup(response.content, 'html.parser')
        dialog = soup.select_one('#account-menu dialog')
        themes = [radio['value'] for radio in dialog.select('input[name="theme"]')]
        self.assertEqual(themes, ['system', 'light', 'dark'])
        self.assertEqual(dialog.select_one('.account-menu__sign-out').get_text(strip=True), 'Sign out')
