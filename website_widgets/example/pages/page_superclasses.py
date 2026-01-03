import hashlib
import inspect
import os
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit

from django.http import HttpRequest, HttpResponse, HttpResponseNotModified
from django.utils.http import http_date, parse_http_date_safe

from website_widgets import Page
from website_widgets.config import get_config
from website_widgets.example.widgets.appbar import ExampleAppbar
from website_widgets.example.widgets.footer import ExampleFooter

class ExamplePageSimple(Page):
    """
    Minimal intermediate class - just sets a default base template.
    Good for simple apps or getting started quickly.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Sub classes can override in set_context()
        self.context.page['title'] = 'Example App'
        self.context.page['show_appbar_back_button'] = False

        # Without setting the appbar and footer widgets here,
        # sub classes can choose whether to include them or not.

    def base_template_path(self) -> str:
        folder_path = os.path.dirname(inspect.getfile(self.__class__))
        return folder_path + '/../templates/base.html'


class ExamplePageComplex(Page):
    """
    Full-featured intermediate class showing real-world patterns.

    Demonstrates:
    - ETag generation for conditional requests (304 Not Modified)
    - Canonical URL generation (strips tracking params)
    - App-wide context setup
    - Custom response building with caching headers
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Sub classes can override in set_context()
        self.context.page['title'] = 'Example App'
        self.context.page['show_appbar_back_button'] = False

    def base_template_path(self) -> str:
        folder_path = os.path.dirname(inspect.getfile(self.__class__))
        return folder_path + '/../templates/base.html'

    async def handle_request(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
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

        # Sub class pages can set `show_appbar_back_button = True` in their own set_context()
        await self.set_context(*args, **kwargs)

        # Add appbar and footer after set_context() so the subclass page can
        # modify `page.show_appbar_back_button` if desired.
        # Subclasses of ExamplePageComplex don't need to set appbar/footer manually.
        self.context.children['appbar'] = ExampleAppbar(parent=self)
        self.context.children['footer'] = ExampleFooter(parent=self)

        # Capture debug tree BEFORE rendering (while children are still Widget objects)
        self._debug_tree_html = None
        if get_config().show_debug_tree:
            self._debug_tree_html = self._generate_debug_tree()

        # Render the widget tree to HTML
        await self._render_children_to_html()

        main_content_html = self.html()

        response = self.build_response(main_content_html)

        if last_modified:
            response['Last-Modified'] = http_date(int(last_modified.timestamp()))
            response['ETag'] = self.generate_etag(last_modified, request)
            response['Cache-Control'] = 'public, max-age=0, must-revalidate'

        return response

    async def set_context(self, *args, **kwargs):
        """App-wide defaults for all pages."""
        self.context.page['title'] = 'Example App'
        self.context.page['canonical_url'] = self.generate_canonical_url(self.request)

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
