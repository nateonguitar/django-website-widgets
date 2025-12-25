import hashlib
from datetime import datetime
import os
from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseNotModified
from django.utils.http import http_date, parse_http_date_safe

from website_widgets import Page
from website_widgets.example.widgets.appbar import ExampleAppbar
from website_widgets.example.widgets.footer import ExampleFooter


class ExampleAppPageSimple(Page):
    """
    Minimal intermediate class - just sets a default base template.
    Good for simple apps or getting started quickly.
    """

    def base_template_path(self) -> str:
        return os.path.join(settings.BASE_DIR, 'website_widgets', 'example', 'templates', 'base1.html')

    async def init_page_state(self, request: HttpRequest, *args, **kwargs):
        await super().init_page_state(request, *args, **kwargs)
        self.context.page.set('title', 'Example App')
        self.context.children.set('appbar', ExampleAppbar(parent=self).html_sync())
        self.context.children.set('footer', ExampleFooter(parent=self).html_sync())


class ExampleAppPageComplex(Page):
    """
    Full-featured intermediate class showing real-world patterns.

    Demonstrates:
    - ETag generation for conditional requests (304 Not Modified)
    - Canonical URL generation (strips tracking params)
    - App-wide context setup
    - Custom response building with caching headers
    """

    def base_template_path(self) -> str:
        return os.path.join(settings.BASE_DIR, 'website_widgets', 'example', 'templates', 'base1.html')

    async def render_page(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self._init_page_state_called = False

        # Check for conditional request (304 Not Modified)
        last_modified = await self.get_last_modified(request, *args, **kwargs)
        if last_modified and request.method == 'GET':
            etag = self.generate_etag(last_modified, request)

            if_none_match = request.META.get('HTTP_IF_NONE_MATCH')
            if if_none_match and etag in if_none_match:
                return HttpResponseNotModified()

            if_modified_since = request.META.get('HTTP_IF_MODIFIED_SINCE')
            if if_modified_since:
                ims_timestamp = parse_http_date_safe(if_modified_since)
                if ims_timestamp and int(last_modified.timestamp()) <= ims_timestamp:
                    return HttpResponseNotModified()

        await self.init_page_state(request, *args, **kwargs)

        if not self._init_page_state_called:
            raise RuntimeError(
                f"{self.__class__.__name__}.init_page_state() must call "
                "super().init_page_state(request, *args, **kwargs) first."
            )

        await self.set_context(*args, **kwargs)

        main_content_html = self.html_sync()

        response = self.build_response(main_content_html)

        if last_modified:
            response['Last-Modified'] = http_date(int(last_modified.timestamp()))
            response['ETag'] = self.generate_etag(last_modified, request)
            response['Cache-Control'] = 'public, max-age=0, must-revalidate'

        return response

    async def init_page_state(self, request: HttpRequest, *args, **kwargs):
        """App-wide defaults for all pages."""
        await super().init_page_state(request, *args, **kwargs)
        self.context.page.set('title', 'Example App')
        self.context.page.set('canonical_url', self.generate_canonical_url(request))
        self.context.children.set('appbar', ExampleAppbar(parent=self).html_sync())
        self.context.children.set('footer', ExampleFooter(parent=self).html_sync())

    async def get_last_modified(self, request: HttpRequest, *args, **kwargs) -> datetime | None:
        """Override in page subclasses to enable conditional requests."""
        return None

    def generate_etag(self, last_modified: datetime, request: HttpRequest) -> str:
        """Generate ETag from timestamp, path, and user."""
        path_hash = hashlib.md5(request.path.encode()).hexdigest()[:8]
        user_id = getattr(request.user, 'id', 0) or 0
        return f'"{int(last_modified.timestamp())}-{path_hash}-{user_id}"'

    def generate_canonical_url(self, request: HttpRequest) -> str:
        """Generate canonical URL, stripping common tracking parameters."""
        TRACKING_PARAMS = {
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'gclid', 'fbclid', 'msclkid', '_ga', '_gl'
        }

        parts = urlsplit(request.get_full_path())
        cleaned_params = []
        if parts.query:
            for param in parts.query.split('&'):
                key = param.split('=')[0] if '=' in param else param
                if key not in TRACKING_PARAMS:
                    cleaned_params.append(param)

        host = request.get_host()
        scheme = 'https' if request.is_secure() else 'http'
        return urlunsplit((scheme, host, parts.path, '&'.join(cleaned_params), ''))
