import os
from urllib.parse import urlencode

from django.http import HttpRequest, HttpResponse
from django.middleware.csrf import get_token
from django.urls import reverse

from website_widgets.example.api.errors import (
    ForbiddenException,
    HttpException,
    NotFoundException,
    UnauthorizedException,
)
from website_widgets.example.example_page.example_page import ExamplePage
from website_widgets.example.projects.flash_cookie import FlashCookie
from website_widgets.example.projects.store import User
from website_widgets.example.projects.viewer_cookie import ViewerCookie
from website_widgets.example.projects.widgets.appbar.appbar import Appbar
from website_widgets.example.projects.widgets.footer.footer import Footer
from website_widgets.example.projects.widgets.projects_stylesheet.projects_stylesheet import ProjectsStylesheet


class ProjectsAppPage(ExamplePage):
    """
    The projects app's base page: its own document template and stylesheet, the appbar, the
    viewer, flash messages, and the access variants.

    The appbar and footer are children of every page, rendered by the document template rather
    than the page's own, so they sit outside `page_content_html`. They still read `context.page`,
    which the page fills before either template renders.

    A page's `set_context()` raises `UnauthorizedException`, `ForbiddenException` or
    `NotFoundException` to refuse the request. This page catches it and renders
    `projects_app_page__<variant>.html` instead, a file kept beside this module and found through
    the class hierarchy for every subclass.
    """

    document_template_path = os.path.join(os.path.dirname(__file__), 'document_template.html')
    stylesheet_class = ProjectsStylesheet

    viewer: User | None = None

    async def handle_request(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        try:
            await self._call_set_context()
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

    def set_context(self):
        super().set_context()
        self.viewer = ViewerCookie.viewer(self.request)
        self.context.page['viewer'] = self.viewer
        self.context.page['csrf_token'] = get_token(self.request)
        self.context.page['flash'] = FlashCookie.read(self.request)
        self.context.page['flash_cookie_name'] = FlashCookie.NAME
        self.context.page['login_url'] = (
            f"{reverse('website_widgets_example_login')}?{urlencode({'next': self.request.get_full_path()})}")
        self._add_chrome()

    def _add_chrome(self):
        self.context.children['stylesheet'] = self.stylesheet_class()
        self.context.children['appbar'] = Appbar()
        self.context.children['footer'] = Footer()

    def _show_access_variant(self, variant: str, error: HttpException):
        """Drops whatever the page built before refusing, keeping only the chrome."""
        self.status_code = error.status_code
        self.template_filename = f'projects_app_page__{variant}.html'
        self.context.data = {'status_code': error.status_code}
        self.context.children = {}
        self._add_chrome()
        self.context.page['title'] = error.message
        self.context.page['description'] = error.message
