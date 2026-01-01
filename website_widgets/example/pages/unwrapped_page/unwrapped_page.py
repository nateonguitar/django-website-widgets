import inspect
import os

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

    Overrides base_template_path() to use a minimal base template.
    """

    async def set_context(self, *args, **kwargs):
        await super().set_context(*args, **kwargs)
        self.context.page['title'] = 'Unwrapped Page'

    def base_template_path(self) -> str:
        folder_path = os.path.dirname(inspect.getfile(self.__class__))
        return folder_path + '/../templates/base_unwrapped.html'
