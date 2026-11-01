from website_widgets import AsyncWidget

from website.widgets.account_menu import AccountMenu


class Appbar(AsyncWidget):
    """
    The bar at the top of every page: the links, the cart's count, and either the signed-in
    user's `AccountMenu` or a link to sign in.
    """

    async def set_context(self):
        # AppPage loaded the user into context.page before any widget ran, and the account menu
        # reads it from there too, so nothing is passed down.
        signed_in = self.context.page['user'].is_authenticated
        # A child only for someone signed in; None renders nothing.
        self.context.children['account_menu'] = AccountMenu() if signed_in else None
