from website_widgets import register_url

from website.models import Article
from website.pages.site_page import SitePage
from website.refusals import NotAllowed, NotLoggedIn


@register_url('editor/', name='editor')
class EditorPage(SitePage):
    """
    Staff only. The check runs before any data is loaded, so a viewer who can't see the page costs
    no queries.
    """

    page_title = 'Editor'

    async def set_context(self):
        await super().set_context()
        if not self.viewer.is_authenticated:
            raise NotLoggedIn()
        if not self.viewer.is_staff:
            raise NotAllowed()
        self.context.data['articles'] = [article async for article in Article.objects.all()]
