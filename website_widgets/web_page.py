from django.http import HttpRequest, HttpResponse
from django.utils.safestring import SafeText, mark_safe
import inspect

from website_widgets.widget import Widget
from website_widgets.config import get_config


class _WebPage(Widget):
    """
    What `AsyncWebPage` and `SyncWebPage` share: a widget that answers a web request at a URL,
    rendering two templates against the same context: its own, found like any widget's, then the
    document template at `document_template_path`, which receives the first as
    `{{ page_content_html }}`. Both see the same `page`, `data` and `children`, so a child widget
    can render in either one.

    Not subclassed directly: a page says which it is by subclassing one of the two.
    """

    status_code: int = 200
    # The whole HTML document, `<head>` included. A real path, unlike `template_filename`, since it
    # is shared rather than kept beside one page. Resolved against the concrete class's folder
    # unless absolute.
    document_template_path: str | None = None
    # The widget tree as HTML, set by `build_response()` when `show_debug_tree` is on.
    _debug_tree_html: str | None = None
    # Set by AsyncWebPage and SyncWebPage: whether set_context(), handle_request() and
    # build_response() are `async def`.
    _renders_async: bool | None = None
    _METHODS_MATCHING_RENDERS_ASYNC = ('set_context', 'handle_request', 'build_response')

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls._renders_async is None:
            raise TypeError(
                f'{cls.__name__} subclasses _WebPage; subclass AsyncWebPage or SyncWebPage instead.')
        for method_name in cls._METHODS_MATCHING_RENDERS_ASYNC:
            is_async = inspect.iscoroutinefunction(getattr(cls, method_name))
            if is_async == cls._renders_async:
                continue
            if cls._renders_async:
                raise TypeError(
                    f'{cls.__name__}.{method_name}() is `def`, but {cls.__name__} is an '
                    f'AsyncWebPage: write `async def {method_name}()`, or subclass SyncWebPage.')
            raise TypeError(
                f'{cls.__name__}.{method_name}() is `async def`, but {cls.__name__} is a '
                f'SyncWebPage: write `def {method_name}()`, or subclass AsyncWebPage.')

    def get_document_template_path(self) -> str:
        """The path to the document wrapping this page's content, from `document_template_path`."""
        if self.document_template_path is None:
            raise NotImplementedError(
                "Subclasses must set `document_template_path` or override "
                "`get_document_template_path()`.")
        return self._resolve_beside_class_file(self.document_template_path)

    def _render_initialized_tree(self) -> HttpResponse:
        """
        After every `set_context()` has run: renders the tree, wraps it in the document template,
        and returns the response.
        """
        # Between the passes: every child is populated, and still a Widget rather than HTML.
        self._debug_tree_html = None
        if get_config().show_debug_tree:
            self._debug_tree_html = self._generate_debug_tree()

        self._render_children_to_html()

        page_content_html = self._render_template()

        if self._debug_tree_html:
            page_content_html = page_content_html + self._debug_tree_panel()

        html = self._render_template(
            template_path=self.get_document_template_path(),
            extra_context={
                'page_content_html': page_content_html,
            })
        return HttpResponse(html, status=self.status_code)

    def _debug_tree_panel(self) -> SafeText:
        return mark_safe(f"""
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
            """)

    @classmethod
    def _store_view_attributes(cls, view, initargs, initkwargs):
        view.view_class = cls
        view.view_initargs = initargs
        view.view_initkwargs = initkwargs
        return view


class AsyncWebPage(_WebPage):
    """
    A page whose `set_context()` is `async def`, so it awaits the ORM's async methods
    (`await Movie.objects.aget(...)`). Its widgets may be either kind. The starter site and the
    generators use it.

        path('my-page/', MyPage.as_view(), name='my_page')

    Override `set_context()` for the page's data and children, `handle_request()` to wrap the whole
    request (exceptions, conditional responses), and `build_response()` to change the response.
    All three are `async def`; a `def` one raises when the class is defined.
    """

    _renders_async = True

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
            return await instance.handle_request(request, *args, **kwargs)

        return cls._store_view_attributes(view, initargs, initkwargs)

    async def set_context(self):
        """The page's data and children. Base implementation does nothing."""
        pass

    async def handle_request(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Runs the page's `set_context()`, then `build_response()`.

        Override to wrap the whole request, such as turning an exception into a variant template:

            try:
                await self.set_context()
            except NotFoundException:
                self.status_code = 404
                self.template_filename = 'my_page__not_found.html'
            return await self.build_response()
        """
        await self.set_context()
        return await self.build_response()

    async def build_response(self) -> HttpResponse:
        """
        Runs every descendant's `set_context()`, awaiting the async ones, renders the tree and
        wraps it in the document template. Override to change the response returned by
        `await super().build_response()`.
        """
        await self._ainitialize_widget_tree()
        return self._render_initialized_tree()


class SyncWebPage(_WebPage):
    """
    A page whose `set_context()` is `def`, so it uses the ORM as any Django view does
    (`Movie.objects.get(...)`). Every widget it holds must have a `def set_context()` too: an
    async one raises when the page renders. Prefer `AsyncWebPage`; this is for a page that has
    no async work and a team that would rather not await.

        path('my-page/', MyPage.as_view(), name='my_page')

    Override `set_context()`, `handle_request()` and `build_response()` as on `AsyncWebPage`, each
    with `def`; an `async def` one raises when the class is defined.
    """

    _renders_async = False

    @classmethod
    def as_view(cls, *initargs, **initkwargs):
        """
        A sync view that constructs a fresh page per request. URL parameters go to both the
        constructor and `handle_request()`, as on `AsyncWebPage`.
        """
        def view(request: HttpRequest, *args, **kwargs):
            instance = cls(*args, *initargs, **kwargs, **initkwargs)
            instance._request = request
            return instance.handle_request(request, *args, **kwargs)

        return cls._store_view_attributes(view, initargs, initkwargs)

    def handle_request(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Runs the page's `set_context()`, then `build_response()`. Override to wrap the whole
        request, as on `AsyncWebPage`, calling `self.set_context()` and `self.build_response()`.
        """
        self.set_context()
        return self.build_response()

    def build_response(self) -> HttpResponse:
        """
        Runs every descendant's `set_context()`, renders the tree and wraps it in the document
        template. A widget whose `set_context()` is `async def` raises here. Override to change
        the response returned by `super().build_response()`.
        """
        self._initialize_widget_tree()
        return self._render_initialized_tree()
