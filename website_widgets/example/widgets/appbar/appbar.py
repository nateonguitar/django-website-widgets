from website_widgets import Widget
from website_widgets.example.pages.nav_item import NavItem
from website_widgets.example.widgets.appbar_title import AppbarTitle


class ExampleAppbar(Widget):
    """Navigation header for the example app."""

    def __init__(self, parent: 'Widget | None' = None):
        super().__init__(parent=parent)
        # Add title widget as a child
        title = self.context.page.get('title', 'Example App')
        self.context.children['title'] = AppbarTitle(title=title, parent=self)

    def html(self):
        nav_item: NavItem = self.context.page.get('nav_item', NavItem.HOME)
        self.context.data['nav_item'] = nav_item
        return self.render_html()
