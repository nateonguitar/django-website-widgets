from website_widgets.example.pages.app_page import ExampleAppPageSimple


class UnwrappedPage(ExampleAppPageSimple):
    """
    Example of an unwrapped page - no header, nav, or footer.

    Some pages don't need the full app shell:
    - Login/signup pages
    - Error pages (404, 500)
    - Print-friendly views
    - Embedded content / iframes
    - Landing pages with custom layouts

    Override base_template_path() to use a minimal base template.
    """

    async def set_context(self, *args, **kwargs):
        self.context.page['title'] = 'Unwrapped Page'

    def base_template_path(self) -> str:
        return 'website_widgets/example/templates/base_unwrapped.html'
