from website_widgets.example.pages.nav_item import NavItem
from website_widgets.example.pages.page_superclasses import ExamplePageSimple
from website_widgets.example.widgets.appbar.appbar import ExampleAppbar
from website_widgets.example.widgets.footer.footer import ExampleFooter


class SimplePage(ExamplePageSimple):
    """
    Minimal example page using the default base template from ExampleAppPage.
    No need to override base_template_path() - it inherits the default.
    """

    async def set_context(self, *args, **kwargs):
        await super().set_context(*args, **kwargs)
        self.context.page['title'] = 'Simple Page'
        self.context.page['nav_item'] = NavItem.SIMPLE_PAGE
        self.context.page['show_appbar_back_button'] = True
        self.context.data['greeting'] = 'Hello from website_widgets!'

        # The Simple super class does not add appbar/footer automatically.
        # The super class uses base.html will try to render both the header and footer,
        # but django's template engine will just ignore missing context children.
        self.context.children['appbar'] = ExampleAppbar(parent=self)
        self.context.children['footer'] = ExampleFooter(parent=self)
