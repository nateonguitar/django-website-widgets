"""
Browser tests with no server: Chromium asks for a page, and Django's test client answers it, on
the test's own database transaction. An example to copy and own, not part of the package; the
package's `browser_testing.md` explains why it is built this way.

Needs Playwright (`poetry install --with playwright`, then `poetry run playwright install
chromium`) and a built frontend (`manage.py ww_test` builds it first), since static files are served
from where the staticfiles finders find them, and a test module importing this one skips itself
when Playwright isn't installed.
"""

import json
import mimetypes
import os
import threading
from pathlib import Path
from urllib.parse import urlsplit

from asgiref.sync import async_to_sync
from django.conf import settings
from django.contrib.staticfiles import finders
from django.db import connections
from django.http import HttpResponse
from django.test import tag
from playwright.sync_api import Browser, Page, Playwright, Route, sync_playwright

from website.tests.app_widget_test_case import AppWidgetTestCase


@tag('playwright')
class PlaywrightTestCase(AppWidgetTestCase):
    """
    A Chromium page whose every request is answered in-process:

    - a request for `HOST` goes to `self.client`, inside the test's transaction, so a test sees
      the browser's writes and the browser sees the test's rows;
    - `STATIC_URL` is read through the staticfiles finders, so no `collectstatic`;
    - every other host is aborted, so nothing reaches the internet. To let a host through, such
      as a font CDN, change `_answer()` where it aborts.

    `goto(path)` opens a page, `open_widget(widget)` a widget alone in `AppWidgetTestCase`'s
    document, `login(user)` signs the browser in, `screenshot(name)` saves a PNG.
    """

    HOST = 'http://testserver'
    # The test-host URL open_document() answers with its HTML. Any path the site doesn't route.
    DOCUMENT_PATH = '/__test_document__'
    SCREENSHOTS_DIR = Path(settings.BASE_DIR) / 'test_screenshots'
    # Milliseconds. Everything answers in-process, so a wait this long means it never will.
    TIMEOUT = 5000
    # Redirects followed for a fetch() before giving up.
    MAX_REDIRECTS = 10

    playwright: Playwright
    browser: Browser
    page: Page

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Playwright's sync API keeps its event loop marked as running on this thread between
        # calls, so Django's async-safety check would refuse every query the test itself makes.
        # Nothing else runs on that loop meanwhile, so the check is switched off for the class.
        cls._previous_async_unsafe = os.environ.get('DJANGO_ALLOW_ASYNC_UNSAFE')
        os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
        # The connections holding the class's transaction and setUpTestData() rows. While
        # Playwright runs, `connections` on this thread (and in the route handler) would hand out
        # new ones outside that transaction, which SQLite answers with "table is locked" and
        # PostgreSQL by not seeing the rows. So the same objects are put back after starting, and
        # the handler's thread borrows them too.
        cls._test_connections = {alias: connections[alias] for alias in connections}
        # One browser per class, about 0.2 s to launch: stopped in tearDownClass, before Django
        # rolls back and closes the database, so the loop is gone by then.
        cls.playwright = sync_playwright().start()
        for alias, connection in cls._test_connections.items():
            connections[alias] = connection
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        if cls._previous_async_unsafe is None:
            os.environ.pop('DJANGO_ALLOW_ASYNC_UNSAFE', None)
        else:
            os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = cls._previous_async_unsafe
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self._document_html = ''
        self.context = self.browser.new_context(base_url=self.HOST)
        self.addCleanup(self.context.close)
        self.context.set_default_timeout(self.TIMEOUT)
        self.context.route('**/*', self._answer)
        self.page = self.context.new_page()

    def goto(self, path: str):
        return self.page.goto(path)

    def login(self, user):
        """Signs the browser in as `user` with Django's session cookie, with no page load."""
        self.client.force_login(user)
        session_cookie = self.client.cookies[settings.SESSION_COOKIE_NAME]
        self.context.add_cookies([{
            'name': settings.SESSION_COOKIE_NAME,
            'value': session_cookie.value,
            'url': self.HOST,
        }])

    def open_document(self, html: str):
        """Opens `html` at `DOCUMENT_PATH` on the test host, so its relative URLs (`/static/main.js`) resolve."""
        self._document_html = html
        return self.page.goto(self.DOCUMENT_PATH)

    def open_widget(self, widget, user=None, document_children: dict | None = None, page_context: dict | None = None):
        """
        Renders `widget` into `AppWidgetTestCase`'s document as `user` and opens it, signing the
        browser in as `user` too, so the widget's requests are made as the user it was rendered for.
        """
        if user is not None:
            self.login(user)
        render = async_to_sync(self.arender_document)
        html = self.outside_playwright_loop(
            lambda: render(widget, user=user, document_children=document_children, page_context=page_context))
        return self.open_document(html)

    def screenshot(self, name: str):
        self.SCREENSHOTS_DIR.mkdir(exist_ok=True)
        path = self.SCREENSHOTS_DIR / f'{type(self).__name__}.{self._testMethodName}.{name}.png'
        self.page.screenshot(path=str(path), full_page=True)
        return path

    def outside_playwright_loop(self, function):
        """
        Calls `function` in a short-lived thread that uses the test's database connections, while
        this thread waits, and returns its result. Anything that calls `async_to_sync()`, as the
        test client does for an async view, refuses to run on this thread while Playwright's loop
        is marked as running here.
        """
        outcome = {}

        def run():
            for alias, connection in self._test_connections.items():
                connection.inc_thread_sharing()
                connections[alias] = connection
            try:
                outcome['result'] = function()
            except BaseException as exception:
                outcome['exception'] = exception
            finally:
                for connection in self._test_connections.values():
                    connection.dec_thread_sharing()

        thread = threading.Thread(target=run)
        thread.start()
        thread.join()
        if 'exception' in outcome:
            raise outcome['exception']
        return outcome['result']

    def _answer(self, route: Route):
        url = urlsplit(route.request.url)
        if f'{url.scheme}://{url.netloc}' != self.HOST:
            route.abort()
            return
        if url.path == self.DOCUMENT_PATH:
            route.fulfill(status=200, headers={'content-type': 'text/html; charset=utf-8'}, body=self._document_html)
            return
        static_prefix = '/' + urlsplit(settings.STATIC_URL).path.lstrip('/')
        if url.path.startswith(static_prefix):
            self._answer_static(route, url.path[len(static_prefix):])
            return
        self._answer_from_client(route)

    def _answer_static(self, route: Route, relative_path: str):
        found = finders.find(relative_path)
        if found is None:
            route.fulfill(status=404, body=b'')
            return
        content_type = mimetypes.guess_type(found)[0] or 'application/octet-stream'
        route.fulfill(status=200, headers={'content-type': content_type}, body=Path(found).read_bytes())

    def _answer_from_client(self, route: Route):
        request = route.request
        response = self.outside_playwright_loop(
            lambda: self._client_response(request.method, request.url, request.headers, request.post_data_buffer))
        location = response.get('Location')
        if response.status_code in (301, 302, 303, 307, 308) and location:
            # Chromium follows a redirect that a route fulfilled straight to the network,
            # skipping this handler, so the redirect is made here instead.
            if request.is_navigation_request():
                # A page that navigates on, as the redirect would have, and is itself routed.
                stand_in = f'<!DOCTYPE html><script>location.replace({json.dumps(location)})</script>'
                route.fulfill(status=200, headers={'content-type': 'text/html; charset=utf-8'}, body=stand_in)
                return
            response = self.outside_playwright_loop(lambda: self._follow_redirects(response, request.headers))
        route.fulfill(status=response.status_code, headers=self._browser_headers(response), body=response.content)

    def _client_response(self, method: str, url: str, headers: dict, body: bytes | None) -> HttpResponse:
        parts = urlsplit(url)
        path = parts.path + (f'?{parts.query}' if parts.query else '')
        extra = {}
        for name, value in headers.items():
            if name == 'content-type':
                extra['content_type'] = value
            elif name not in ('content-length', 'host'):
                # The browser's Cookie header replaces the test client's own cookies.
                extra['HTTP_' + name.upper().replace('-', '_')] = value
        return self.client.generic(method, path, data=body or b'', **extra)

    def _follow_redirects(self, response: HttpResponse, headers: dict) -> HttpResponse:
        for _ in range(self.MAX_REDIRECTS):
            location = response.get('Location')
            if response.status_code not in (301, 302, 303, 307, 308) or not location:
                return response
            response = self._client_response('GET', location, headers, None)
        raise RuntimeError(f'More than {self.MAX_REDIRECTS} redirects')

    @staticmethod
    def _browser_headers(response: HttpResponse) -> dict:
        headers = dict(response.items())
        set_cookies = [morsel.OutputString() for morsel in response.cookies.values()]
        if set_cookies:
            # One header holding every cookie, a line each, which Playwright splits again.
            headers['set-cookie'] = '\n'.join(set_cookies)
        return headers
