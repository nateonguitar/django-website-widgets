from website_widgets import register_url

from website.endpoints.article_cards_endpoint import ArticleCardsEndpoint
from website.models import Article
from website.pages.site_page import SitePage
from website.widgets.article_card.article_card import ArticleCard


@register_url('articles/', name='articles')
class ArticlesPage(SitePage):
    """The first page of articles; its "load more" button fetches the rest from the endpoint."""

    page_title = 'Articles'

    async def set_context(self):
        await super().set_context()
        page_size = ArticleCardsEndpoint.PAGE_SIZE
        articles = [article async for article in Article.objects.all()[:page_size + 1]]
        self.context.children['cards'] = [ArticleCard(article=article) for article in articles[:page_size]]
        self.context.data['next_offset'] = page_size
        self.context.data['has_more'] = len(articles) > page_size
