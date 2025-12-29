from website_widgets import Widget
from website_widgets.example.pages.nav_item import NavItem


class ExampleAppbar(Widget):
    """Navigation header for the example app."""

    def html_sync(self):
        nav_item: NavItem = self.context.data.get('nav_item', NavItem.HOME)
        self.context.data['nav_item'] = nav_item
        return self.render_html()
