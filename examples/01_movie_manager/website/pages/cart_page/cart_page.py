from website_widgets import register_url

from website.exceptions import UnauthorizedException
from website.pages.app_page import AppPage


@register_url('cart')
class CartPage(AppPage):
    """The cart itself is in the browser's localStorage, so the page has nothing to load."""

    page_title = 'Cart'

    async def set_context(self):
        if not self.context.page['user'].is_authenticated:
            raise UnauthorizedException('Sign in to see your cart.')
