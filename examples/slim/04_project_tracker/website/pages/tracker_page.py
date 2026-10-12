import os
from urllib.parse import urlencode

from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.http import HttpRequest, HttpResponse
from django.middleware.csrf import get_token
from django.urls import reverse

from website_widgets import WebPage

from website.api.errors import (
    ForbiddenException,
    HttpException,
    NotFoundException,
    UnauthorizedException,
)
from website.flash_cookie import FlashCookie
from website.widgets.appbar.appbar import Appbar
from website.widgets.footer.footer import Footer


class TrackerPage(WebPage):
    """
    The tracker's base page: the document template, the appbar and footer, the viewer, flash
    messages, and the access variants. It has no `@register_url`, so it isn't routed.

    The appbar and footer are children of every page, rendered by the document template rather
    than the page's own, so they sit outside `page_content_html`. They still read `context.page`,
    which the page fills before either template renders.

    A page's `set_context()` raises `UnauthorizedException`, `ForbiddenException` or
    `NotFoundException` to refuse the request. This page catches it and renders
    `tracker_page__<variant>.html` instead, a file kept beside this module and found through the
    class hierarchy for every subclass.
    """

    # Absolute: a relative path resolves beside each page's own module, not this one.
    document_template_path = os.path.join(os.path.dirname(__file__), 'document_template.html')
    SITE_NAME = 'Project tracker'

    page_title = SITE_NAME
    page_description = 'A small project tracker built with django-website-widgets.'
    viewer: AbstractBaseUser | AnonymousUser | None = None

    async def handle_request(
        self,
        request: HttpRequest,
        *args,
        **kwargs
    ) -> HttpResponse:
        try:
            await self._acall_set_context()
        except UnauthorizedException as error:
            self._show_access_variant('unauthorized', error)
        except ForbiddenException as error:
            self._show_access_variant('forbidden', error)
        except NotFoundException as error:
            self._show_access_variant('not_found', error)
        return await self.build_response()

    async def build_response(self) -> HttpResponse:
        response = await super().build_response()
        FlashCookie.clear(self.request, response)
        return response

    async def set_context(self):
        # Fetched with the async API: evaluating the lazy `request.user` in a template would run
        # a synchronous session query inside the page.
        self.viewer = await self.request.auser()
        self.context.page['site_name'] = self.SITE_NAME
        self.context.page['title'] = self.page_title
        self.context.page['description'] = self.page_description
        self.context.page['viewer'] = self.viewer if self.viewer.is_authenticated else None
        # Widget templates get no context processors, so the token reaches api.js through a <meta>.
        self.context.page['csrf_token'] = get_token(self.request)
        self.context.page['flash'] = FlashCookie.read(self.request)
        self.context.page['flash_cookie_name'] = FlashCookie.NAME
        login_query = urlencode({'next': self.request.get_full_path()})
        self.context.page['login_url'] = f"{reverse('website:LoginPage')}?{login_query}"
        self._add_chrome()

    def _add_chrome(self):
        self.context.children['appbar'] = Appbar()
        self.context.children['footer'] = Footer()

    def _show_access_variant(
        self,
        variant: str,
        error: HttpException
    ):
        """Drops whatever the page built before refusing, keeping only the chrome."""
        self.status_code = error.status_code
        self.template_filename = f'tracker_page__{variant}.html'
        self.context.data = {'status_code': error.status_code}
        self.context.children = {}
        self._add_chrome()
        self.context.page['title'] = error.message
        self.context.page['description'] = error.message
