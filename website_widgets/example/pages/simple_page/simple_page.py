from website_widgets.example.pages.app_page import ExampleAppPageSimple


class SimplePage(ExampleAppPageSimple):
    """
    Minimal example page using the default base template from ExampleAppPage.
    No need to override base_template_path() - it inherits the default.
    """

    async def set_context(self, *args, **kwargs):
        self.context.page['title'] = 'Simple Page'
        self.context.page['show_parent_link'] = True
        self.context.data['greeting'] = 'Hello from website_widgets!'
