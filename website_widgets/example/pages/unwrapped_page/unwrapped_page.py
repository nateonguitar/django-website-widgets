from website_widgets.page import Page


class UnwrappedPage(Page):
    """
    Example of an unwrapped page - no header, nav, or footer.

    Some pages don't need the full app shell:
    - Login/signup pages
    - Error pages (404, 500)
    - Print-friendly views
    - Embedded content / iframes
    - Landing pages with custom layouts

    Sets base_template_path to use a minimal base template.
    """

    base_template_path = '../templates/base_unwrapped.html'

    def set_context(self):
        super().set_context()
        self.context.page['title'] = 'Unwrapped Page'
