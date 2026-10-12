from django.http import HttpRequest, HttpResponse
from django.utils.safestring import mark_safe
from django.conf import settings
import inspect

from website_widgets.widget import Widget
from website_widgets.config import get_config


class WebPage(Widget):
    """
    A widget that answers a web request at a URL, rendering two templates against the same
    context: its own, found
    like any widget's, then the document template at `document_template_path`, which receives the
    first as `{{ page_content_html }}`. Both see the same `page`, `data` and `children`, so a child
    widget can render in either one.

        path('my-page/', MyPage.as_view(), name='my_page')

    Override `set_context()` for the page's data and children, `handle_request()` to wrap the whole
    request (exceptions, conditional responses), and `build_response()` to change the response.
    """

    status_code: int = 200
    # The whole HTML document, `<head>` included. A real path, unlike `template_filename`, since it
    # is shared rather than kept beside one page. Resolved against the concrete class's folder
    # unless absolute.
    document_template_path: str | None = None
    # The widget tree as HTML, set by `build_response()` when `show_debug_tree` is on.
    _debug_tree_html: str | None = None

    @classmethod
    def as_view(cls, *initargs, **initkwargs):
        """
        An async view that constructs a fresh page per request. URL parameters go to both the
        constructor and `handle_request()`, so a page can keep them as attributes:

            path('profile/<str:username>/', ProfilePage.as_view(), name='profile')
        """
        async def view(request: HttpRequest, *args, **kwargs):
            instance = cls(*args, *initargs, **kwargs, **initkwargs)
            instance._request = request
            if inspect.iscoroutinefunction(instance.handle_request):
                return await instance.handle_request(request, *args, **kwargs)
            else:
                return instance.handle_request(request, *args, **kwargs)

        view.view_class = cls
        view.view_initargs = initargs
        view.view_initkwargs = initkwargs
        return view

    def get_document_template_path(self) -> str:
        """The path to the document wrapping this page's content, from `document_template_path`."""
        if self.document_template_path is None:
            raise NotImplementedError(
                "Subclasses must set `document_template_path` or override "
                "`get_document_template_path()`.")
        return self._resolve_beside_class_file(self.document_template_path)

    async def handle_request(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Runs the page's `set_context()`, then `build_response()`. Sync or async.

        Override to wrap the whole request, such as turning an exception into a variant template:

            try:
                await self._acall_set_context()
            except NotFoundException:
                self.status_code = 404
                self.template_filename = 'my_page__not_found.html'
            return await self.build_response()
        """
        await self._acall_set_context()
        return await self.build_response()

    async def build_response(self) -> HttpResponse:
        """
        Renders the widget tree and wraps it in the document template. Override to change the response
        returned by `await super().build_response()`.
        """
        await self._ainitialize_widget_tree()

        # Between the passes: every child is populated, and still a Widget rather than HTML.
        self._debug_tree_html = None
        if get_config().show_debug_tree:
            self._debug_tree_html = self._generate_debug_tree()

        self._render_children_to_html()

        page_content_html = self._render_template()

        if self._debug_tree_html:
            debug_tree_html = f"""
            <div style="margin-top: 40px; padding: 20px; background: #f5f5f5; border-top: 2px solid #ddd; font-family: monospace; font-size: 14px; box-sizing: border-box; width: 100%; max-width: 100%;">
                <h3 style="margin-top: 0; color: #333;">Widget Tree Debug View</h3>
                <div style="background: white; padding: 15px; border-radius: 4px; border: 1px solid #ddd; overflow-x: auto; word-wrap: break-word; box-sizing: border-box;">
                    {self._debug_tree_html}
                </div>
            </div>
            <style>
                @media (max-width: 768px) {{
                    div[style*="Widget Tree Debug"] {{
                        padding: 12px !important;
                        font-size: 12px !important;
                    }}
                }}
            </style>
            """
            page_content_html = page_content_html + mark_safe(debug_tree_html)

        html = self._render_template(
            template_path=self.get_document_template_path(),
            extra_context={
                'page_content_html': page_content_html,
            })
        return HttpResponse(html, status=self.status_code)
