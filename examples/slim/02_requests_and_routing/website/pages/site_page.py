import os
from urllib.parse import urlencode

from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.http import HttpRequest, HttpResponse
from django.middleware.csrf import get_token
from django.urls import reverse

from website_widgets import WebPage

from website.refusals import PageRefusal
from website.widgets.site_header.site_header import SiteHeader


class SitePage(WebPage):
    """
    The base of every page here. It has no `@register_url`, so it isn't routed.

    A page's `set_context()` raises a `PageRefusal` (`NotLoggedIn`, `NotAllowed`, `NotFound`) to
    refuse the request. `handle_request()` catches it and renders `site_page__<variant>.html` with
    the refusal's status code instead: a variant template kept beside this module, which the
    template lookup finds for every subclass.
    """

    # Absolute: a relative path resolves beside each page's own module, not this one.
    document_template_path = os.path.join(os.path.dirname(__file__), 'document_template.html')
    SITE_NAME = 'Requests and routing'

    # Left unset, the tab shows only the site's name, as the home page's does.
    page_title: str | None = None
    page_description = 'django-website-widgets example: how a request reaches a page, and how a page answers.'
    viewer: AbstractBaseUser | AnonymousUser | None = None

    async def handle_request(
        self,
        request: HttpRequest,
        *args,
        **kwargs
    ) -> HttpResponse:
        try:
            await self._acall_set_context()
        except PageRefusal as refusal:
            self._show_refusal(refusal)
        return await self.build_response()

    async def set_context(self):
        # Fetched with the async API: evaluating the lazy `request.user` in a template would run
        # a synchronous session query inside the page.
        self.viewer = await self.request.auser()
        self.context.page['site_name'] = self.SITE_NAME
        self.context.page['title'] = self.page_title
        self.context.page['description'] = self.page_description
        self.context.page['viewer'] = self.viewer if self.viewer.is_authenticated else None
        # Widget templates get no context processors, so `{% csrf_token %}` is empty in them.
        self.context.page['csrf_token'] = get_token(self.request)
        self.context.page['index_url'] = reverse('website:IndexPage')
        login_query = urlencode({'next': self.request.get_full_path()})
        self.context.page['login_url'] = f"{reverse('login')}?{login_query}"
        self.context.children['site_header'] = SiteHeader()

    def _show_refusal(self, refusal: PageRefusal):
        """Drops whatever the page built before refusing, keeping only the header."""
        self.status_code = refusal.status_code
        self.template_filename = f'site_page__{refusal.variant}.html'
        self.context.data = {'status_code': refusal.status_code}
        self.context.children = {'site_header': SiteHeader()}
        self.context.page['title'] = refusal.title
