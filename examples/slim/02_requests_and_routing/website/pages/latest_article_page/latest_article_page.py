from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse

from website_widgets import register_url

from website.models import Article
from website.pages.site_page import SitePage
from website.refusals import NotFound


@register_url('articles/latest/', name='latest_article')
class LatestArticlePage(SitePage):
    """
    Redirects to the newest article without building any widgets, from `handle_request()`.

    Its route also shows the ordering rule: `articles/latest/` and `articles/<slug:slug>/` could
    both match `/articles/latest/`, and the fixed segment is tried first, wherever either page is
    declared. `ww_show_routes` lists the two in that order.
    """

    async def handle_request(
        self,
        request: HttpRequest,
        *args,
        **kwargs
    ) -> HttpResponse:
        newest = await Article.objects.order_by('-published_at').afirst()
        if newest is not None:
            article_url = reverse('website:article', kwargs={'slug': newest.slug})
            return HttpResponseRedirect(article_url)
        return await super().handle_request(request, *args, **kwargs)

    async def set_context(self):
        await super().set_context()
        raise NotFound()
