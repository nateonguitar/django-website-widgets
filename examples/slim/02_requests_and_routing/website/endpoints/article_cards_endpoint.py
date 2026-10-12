from django.http import HttpRequest, JsonResponse
from django.views import View

from website.models import Article
from website.widgets.article_card.article_card import ArticleCard


class ArticleCardsEndpoint(View):
    """
    `GET ?offset=N` returns the next articles' cards as HTML, rendered on the server with
    `arender()`, for the articles page to add under the others: the pattern behind a "load more"
    button or an infinite scroller. A plain Django view, routed by hand in `urls.py`.
    """

    PAGE_SIZE = 3

    async def get(self, request: HttpRequest) -> JsonResponse:
        raw_offset = request.GET.get('offset', '0')
        offset = int(raw_offset) if raw_offset.isdigit() else 0
        articles = [
            article
            async for article in Article.objects.all()[offset:offset + self.PAGE_SIZE + 1]
        ]
        shown_articles = articles[:self.PAGE_SIZE]
        card_htmls = [await ArticleCard(article=article).arender(request) for article in shown_articles]
        return JsonResponse({
            'html': ''.join(card_htmls),
            'next_offset': offset + len(shown_articles),
            'has_more': len(articles) > self.PAGE_SIZE,
        })
