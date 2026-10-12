from datetime import datetime

from django.db.models import Count, Max
from django.http import HttpRequest, HttpResponse, HttpResponseNotModified
from django.utils.http import parse_etags

from website_widgets import register_url

from website.models import Article
from website.pages.site_page import SitePage


@register_url('changelog/', name='changelog')
class ChangelogPage(SitePage):
    """
    Answers 304 Not Modified when the browser already holds the current version, before any
    widget is built. The ETag comes from the articles themselves: how many there are and when the
    newest change was made, so editing or adding one changes it.

    The page's HTML also shows who is logged in, so the ETag includes the viewer and the response
    varies by cookie; a page that didn't would leave them out.
    """

    page_title = 'Changelog'

    async def handle_request(
        self,
        request: HttpRequest,
        *args,
        **kwargs
    ) -> HttpResponse:
        etag = await self._etag(request)
        if etag in parse_etags(request.headers.get('If-None-Match', '')):
            response = HttpResponseNotModified()
        else:
            response = await super().handle_request(request, *args, **kwargs)
        response['ETag'] = etag
        response['Cache-Control'] = 'no-cache'
        response['Vary'] = 'Cookie'
        return response

    async def set_context(self):
        await super().set_context()
        self.context.data['articles'] = [article async for article in Article.objects.order_by('-updated_at')]
        self.context.data['etag'] = await self._etag(self.request)

    @staticmethod
    async def _etag(request: HttpRequest) -> str:
        summary = await Article.objects.aaggregate(count=Count('id'), newest=Max('updated_at'))
        newest: datetime | None = summary['newest']
        newest_stamp = int(newest.timestamp()) if newest else 0
        viewer = await request.auser()
        return f'"articles-{summary["count"]}-{newest_stamp}-viewer-{viewer.pk or 0}"'
