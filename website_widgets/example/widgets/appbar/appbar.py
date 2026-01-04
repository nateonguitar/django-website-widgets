from website_widgets import Widget
from website_widgets.example.pages.nav_item import NavItem
from website_widgets.example.widgets.appbar_title import AppbarTitle


class ExampleAppbar(Widget):
    """Navigation header for the example app."""

    def set_context(self):
        title = self.context.page.get('title', 'Example App')
        self.context.children['title'] = AppbarTitle(title=title)
