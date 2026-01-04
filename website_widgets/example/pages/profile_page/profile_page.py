from website_widgets.example.pages.nav_item import NavItem
from website_widgets.example.pages.page_superclasses import ExamplePageSimple
from website_widgets.example.widgets.appbar.appbar import ExampleAppbar
from website_widgets.example.widgets.footer.footer import ExampleFooter


class ProfilePage(ExamplePageSimple):
    """
    Example page demonstrating URL path parameters passed to constructor.
    The username comes from the URL pattern and is stored as an instance variable.
    """

    def __init__(self, username: str):
        super().__init__()
        self.username = username

    def set_context(self):
        super().set_context()

        self.context.page['title'] = f'Profile: {self.username}'
        self.context.page['nav_item'] = NavItem.HOME
        self.context.page['show_appbar_back_button'] = True

        self.context.data['username'] = self.username
        self.context.data['profile_info'] = {
            'member_since': '2024',
            'favorite_color': 'blue' if len(self.username) % 2 == 0 else 'red',
            'post_count': len(self.username) * 42,
        }

        self.context.children['appbar'] = ExampleAppbar()
        self.context.children['footer'] = ExampleFooter()
