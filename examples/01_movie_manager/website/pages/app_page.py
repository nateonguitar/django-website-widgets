import os

from django.http import HttpRequest, HttpResponse
from django.middleware.csrf import get_token
from website_widgets import AsyncWebPage

from website.exceptions import (
    ForbiddenException,
    NotFoundException,
    RedirectException,
    UnauthorizedException,
)
from website.widgets.app_urls import AppUrls
from website.widgets.appbar import Appbar
from website.widgets.confirm_dialog import ConfirmDialog


class AppPage(AsyncWebPage):
    """
    The base class of every page in this app, and the class `ww_create_page` generates pages
    from. It renders each page into `document_template.html`, adds the widgets every page's
    document shows, and turns the exceptions in `exceptions.py` into a status code and a variant
    template.
    """

    # Absolute, since a relative path would resolve beside each page's own module.
    document_template_path = os.path.join(os.path.dirname(__file__), 'document_template.html')

    SITE_NAME = 'Movie Manager'
    # The appbar's account dialog stores the choice in this cookie, ts/theme.ts writing it. Named
    # for the site, since cookies aren't kept apart by port: another project on localhost would
    # share a plain `theme`.
    THEME_COOKIE = 'movie_manager_theme'
    THEMES = ('system', 'light', 'dark')
    # A page sets its own, as a class attribute or in set_context().
    page_title: str | None = None

    async def handle_request(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        # Before set_context(), so a page can refuse a signed-out visitor, and the refusal pages
        # still show who is signed in. Django's request.user is lazy and would query the session
        # inside this async pipeline, so the user is loaded the async way, once.
        self.context.page['user'] = await request.auser()
        # A widget template gets no context processors, so {% csrf_token %} is empty there. The
        # document template hands this to AppState for every controller's POST.
        self.context.page['csrf_token'] = get_token(request)
        # Read here and written on <html> by the document template, so the page arrives in its
        # theme: set by a script after load instead, a dark page would flash light first.
        theme = request.COOKIES.get(self.THEME_COOKIE)
        self.context.page['theme'] = theme if theme in self.THEMES else 'system'
        try:
            await self.set_context()
        except UnauthorizedException as exception:
            self.status_code = exception.status_code
            self.template_filename = 'app_page__unauthorized.html'
            self.page_title = 'Sign in'
            # set_context() stopped partway, so nothing it set is kept.
            self.context.data = {'message': str(exception)}
            self.context.children = {}
        except ForbiddenException as exception:
            self.status_code = exception.status_code
            self.template_filename = 'app_page__forbidden.html'
            self.page_title = 'Forbidden'
            self.context.data = {'message': str(exception)}
            self.context.children = {}
        except NotFoundException as exception:
            self.status_code = exception.status_code
            self.template_filename = 'app_page__not_found.html'
            self.page_title = 'Not found'
            self.context.data = {'message': str(exception)}
            self.context.children = {}
        except RedirectException as exception:
            return exception.redirect_response

        self.context.page['title'] = self.full_title()
        # The document template hands it to AppState, for every controller.
        self.context.page['site_name'] = self.SITE_NAME
        # Rendered by the document template, so every page has them.
        self.context.children['app_urls'] = AppUrls()
        self.context.children['appbar'] = Appbar()
        self.context.children['confirm_dialog'] = ConfirmDialog()
        return await self.build_response()

    def full_title(self) -> str:
        if self.page_title is None:
            return self.SITE_NAME
        return f'{self.page_title} | {self.SITE_NAME}'
