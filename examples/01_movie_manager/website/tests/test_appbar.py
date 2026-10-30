from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from api.models import User
from website.widgets.appbar import Appbar


class AppbarTestCase(TestCase):
    async def render_appbar(self, user) -> str:
        appbar = Appbar()
        # What AppPage puts in context.page before any widget runs.
        appbar.context.page['user'] = user
        appbar.context.page['site_name'] = 'Movie Manager'
        # arender, since the appbar and its menu have async set_context()s.
        return await appbar.arender__test(user=user)

    async def test_appbar__holds_the_account_menu_with_its_own_controller__when_signed_in(self):
        html = await self.render_appbar(await User.objects.aget(username='alex'))

        soup = BeautifulSoup(html, 'html.parser')
        menu_button = soup.select_one('#appbar #account-menu .account-menu__button')
        self.assertEqual(menu_button.get_text(strip=True), 'alex')
        # Each widget starts its own controller.
        self.assertIn("await AccountMenuController.initializeController('#account-menu');", html)
        self.assertIn("await AppbarController.initializeController('#appbar');", html)

    async def test_appbar__has_no_account_menu__when_signed_out(self):
        html = await self.render_appbar(AnonymousUser())

        soup = BeautifulSoup(html, 'html.parser')
        self.assertIsNone(soup.select_one('#account-menu'))
        sign_in = soup.select_one('.appbar__links a[href^="/sign-in"]')
        self.assertEqual(sign_in.get_text(strip=True), 'Sign in')
