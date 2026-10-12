from website_widgets import register_url

from website.models import Article
from website.pages.site_page import SitePage
from website.refusals import NotFound, NotLoggedIn


@register_url('articles/<slug:slug>/', name='article')
class ArticlePage(SitePage):
    """One article: the 404 variant when the slug matches nothing, the 401 one for a logged-out
    reader of a members-only article."""

    def __init__(self, slug: str):
        super().__init__()
        self.slug = slug

    async def set_context(self):
        await super().set_context()
        article = await Article.objects.filter(slug=self.slug).afirst()
        if article is None:
            raise NotFound()
        if article.members_only and not self.viewer.is_authenticated:
            raise NotLoggedIn()
        self.context.page['title'] = article.title
        self.context.page['description'] = article.summary
        self.context.data['article'] = article
