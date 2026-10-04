from django.http import HttpRequest, HttpResponse, HttpResponseNotModified
from django.utils.http import parse_etags

from website_widgets.example.advanced.pages.advanced_demo_page.advanced_demo_page import AdvancedDemoPage


class ConditionalPage(AdvancedDemoPage):
    """
    Answers 304 Not Modified when the browser already holds the current version, before any
    widget is built. `?version=N` stands in for what a real page would derive its ETag from, such
    as its content's last-modified time.
    """

    async def handle_request(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        etag = self._etag(request)
        if etag in parse_etags(request.headers.get('If-None-Match', '')):
            response = HttpResponseNotModified()
        else:
            response = await super().handle_request(request, *args, **kwargs)
        response['ETag'] = etag
        response['Cache-Control'] = 'no-cache'
        return response

    def set_context(self):
        super().set_context()
        self.context.page['title'] = 'Conditional response'
        self.context.page['description'] = 'An ETag, and a 304 Not Modified when nothing changed.'
        self.context.data['version'] = int(self._version(self.request))
        self.context.data['etag'] = self._etag(self.request)

    @staticmethod
    def _version(request: HttpRequest) -> str:
        version = request.GET.get('version', '1')
        return version if version.isdigit() and len(version) <= 6 else '1'

    @classmethod
    def _etag(cls, request: HttpRequest) -> str:
        return f'"example-v{cls._version(request)}"'
