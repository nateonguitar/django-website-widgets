from __future__ import annotations
import inspect
from django.apps import apps
from django.conf import settings
from django.http import HttpRequest
from django.template import Template, Context
from django.utils.safestring import SafeText
import os
from website_widgets.widget_context import WidgetContext

class _Widget:
    """
    What `AsyncWidget`, `SyncWidget` and the page classes share. Not subclassed directly: a widget
    says which kind it is by subclassing `AsyncWidget` or `SyncWidget`.
    """

    template_filename: str | None = None
    # Shown beside the class name in the debug tree, to tell instances apart: TabCard(42).
    debug_label: object | None = None
    # Library base classes, whose folders hold no application templates.
    _LIBRARY_MODULES = ('website_widgets.widget', 'website_widgets.web_page')
    # Set by the async and sync classes: whether the methods below are `async def`.
    _renders_async: bool | None = None
    _METHODS_MATCHING_RENDERS_ASYNC: tuple[str, ...] = ('set_context',)
    # The async and sync class names, for the error naming the fix.
    _KIND_NAMES = ('AsyncWidget', 'SyncWidget')

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.__module__ in cls._LIBRARY_MODULES:
            return
        async_name, sync_name = cls._KIND_NAMES
        if cls._renders_async is None:
            raise TypeError(
                f'{cls.__name__} subclasses a private base; subclass {async_name} or {sync_name} '
                f'instead.')
        for method_name in cls._METHODS_MATCHING_RENDERS_ASYNC:
            is_async = inspect.iscoroutinefunction(getattr(cls, method_name))
            if is_async == cls._renders_async:
                continue
            if cls._renders_async:
                raise TypeError(
                    f'{cls.__name__}.{method_name}() is `def`, but {cls.__name__} is an '
                    f'{async_name}: write `async def {method_name}()`, or subclass {sync_name}.')
            raise TypeError(
                f'{cls.__name__}.{method_name}() is `async def`, but {cls.__name__} is a '
                f'{sync_name}: write `def {method_name}()`, or subclass {async_name}.')

    def __init__(self):
        """
        Widget constructor. Store data parameters as instance attributes.

        Pattern:
            def __init__(self, user: User, title: str):
                super().__init__()
                self.user = user
                self.title = title

        The system sets self._request and self.context.page automatically
        before calling set_context().
        """
        self._request: HttpRequest | None = None
        self._children_rendered = False
        self.context = WidgetContext()

    @property
    def request(self) -> HttpRequest:
        """
        The HttpRequest being rendered, assigned by the parent before `set_context()` runs.

        What `request.user` holds is up to the project's middleware. Django's
        `AuthenticationMiddleware` makes it lazy: its first read queries the database, which
        raises `SynchronousOnlyOperation` inside a page's async pipeline, so with it a page loads
        the user with `await self.request.auser()`. A middleware that sets an already loaded user
        makes `request.user` safe to read. See `rendering_pipeline.md`. For a custom user model,
        type hint locally for IDE support:

        ```python
        from api.models import User
        request_user: User = await self.request.auser()
        request_user.custom_method()
        ```
        """
        if self._request is not None:
            return self._request
        raise RuntimeError(
            f"{type(self).__name__}.request isn't set until rendering starts, so it can't be read "
            f"in __init__(); read it in set_context() (or a page's handle_request()). It comes "
            f"from the page rendering this widget, or the request passed to render() or "
            f"arender().")

    def set_context(self):
        """
        Lifecycle hook for setting up widget context.
        Called after __init__, before rendering.

        Use this to:
        - Set self.context.data for template variables
        - Create self.context.children widgets
        - Fetch data asynchronously (if using async def)
        - Set self.context.page values if needed

        Patterns:
            # Sync version (use when no async operations needed)
            def set_context(self):
                self.context.data['title'] = self.title
                self.context.children['child'] = SomeWidget()

            # Async version (use when fetching data with await)
            async def set_context(self):
                data = await SomeModel.objects.aget(pk=self.some_id)
                self.context.data['item'] = data
                self.context.children['child'] = SomeWidget(data=data)

        An `AsyncWidget` writes `async def`, a `SyncWidget` plain `def`; the wrong kind raises
        when the class is defined. A widget rendered with `render()`, or in a `SyncWebPage`, is a
        `SyncWidget`. Base implementation does nothing.
        """
        pass

    def render(
        self,
        request: HttpRequest | None = None
    ) -> SafeText:
        """
        Render this widget on its own from synchronous code: an ordinary Django view, an admin
        hook, an email body. The result drops into any Django template unescaped.

        Construct the widget, adjust it if needed, then call this once:

            widget = ProjectListTile(project=project)
            # Provide any custom values the widget might need.
            widget.context.page['foo'] = bar
            html = widget.render(request)

        Runs the whole lifecycle with no event loop: this widget's `set_context()`, every
        descendant's, then the templates, so synchronous ORM calls work in `set_context()`. Raises
        on an `AsyncWidget`; await `arender()` for those. Values put
        in `context.page` beforehand reach every descendant. No document template wraps the
        result.

        Without a request, `self.request` raises, so a widget that needs one fails loudly.
        """
        self._start_rendering(request)
        self._call_set_context()
        self._initialize_widget_tree()
        self._render_children_to_html()
        return self._render_template()

    async def arender(
        self,
        request: HttpRequest | None = None
    ) -> SafeText:
        """
        `render()` for async code, such as an endpoint returning an HTML fragment. Awaits each
        `async def set_context()` and calls each plain one, as a page's pipeline does.
        """
        self._start_rendering(request)
        await self._acall_set_context()
        await self._ainitialize_widget_tree()
        self._render_children_to_html()
        return self._render_template()

    def render__test(
        self,
        user=None
    ) -> SafeText:
        """
        `render()` against a mock `GET /` request, for tests only. `user` becomes `request.user`;
        without one it is `AnonymousUser` when `django.contrib.auth` is installed.
        """
        return self.render(self._build_test_request(user))

    async def arender__test(self, user=None) -> SafeText:
        """`arender()` against a mock `GET /` request, for tests only, like `render__test()`."""
        return await self.arender(self._build_test_request(user))

    @staticmethod
    def _build_test_request(user) -> HttpRequest:
        from django.test import RequestFactory

        request = RequestFactory().get('/')
        if user is not None:
            request.user = user
        elif apps.is_installed('django.contrib.auth'):
            from django.contrib.auth.models import AnonymousUser
            request.user = AnonymousUser()
        return request

    def _start_rendering(
        self,
        request: HttpRequest | None
    ):
        if self._children_rendered:
            raise RuntimeError(
                f'{type(self).__name__} has already been rendered; rendering replaces its children '
                f'with their HTML, so construct a new instance to render again.')
        self._request = request

    def _call_set_context(self):
        if inspect.iscoroutinefunction(self.set_context):
            raise TypeError(
                f'{type(self).__name__}.set_context() is async, so a sync render cannot run it: '
                f'render() and a SyncWebPage run every set_context() without an event loop. '
                f'Await arender() or put it in an AsyncWebPage instead, or write set_context() '
                f'with def.')
        self.set_context()

    async def _acall_set_context(self):
        if inspect.iscoroutinefunction(self.set_context):
            await self.set_context()
        else:
            self.set_context()

    def _initialize_widget_tree(self):
        """Pass 1 for `render()`: every descendant's `set_context()`, parent before child."""
        for widget in self._child_widgets():
            self._share_render_state_with(widget)
            widget._call_set_context()
            widget._initialize_widget_tree()

    async def _ainitialize_widget_tree(self):
        """Pass 1 for pages and `arender()`: every descendant's `set_context()`, parent before child."""
        for widget in self._child_widgets():
            self._share_render_state_with(widget)
            await widget._acall_set_context()
            await widget._ainitialize_widget_tree()

    def _child_widgets(self) -> list[_Widget]:
        widgets = []
        for key, value in self.context.children.items():
            if isinstance(value, list):
                for widget in value:
                    if not isinstance(widget, _Widget):
                        raise TypeError(f"Expected a widget in children['{key}'] list, got {type(widget)}")
                    self._refuse_page_child(widget, key)
                    widgets.append(widget)
            elif isinstance(value, _Widget):
                self._refuse_page_child(value, key)
                widgets.append(value)
        return widgets

    def _refuse_page_child(
        self,
        widget: _Widget,
        key: str
    ):
        # Imported here: web_page.py imports this module. Both are loaded by the time a render runs.
        from website_widgets.web_page import _WebPage

        if isinstance(widget, _WebPage):
            raise TypeError(
                f"{type(widget).__name__} is a page in {type(self).__name__}.context.children"
                f"['{key}']: a page is only ever the root, rendered by its view. Render a widget "
                f"there instead.")

    def _share_render_state_with(self, widget: _Widget):
        # Request and page context are shared by reference across the whole tree.
        widget._request = self._request
        if widget.context.page is not self.context.page and widget.context.page:
            raise RuntimeError(
                f"{type(widget).__name__}.context.page was written before {type(self).__name__} "
                f"rendered it, so its keys {sorted(widget.context.page)} would be lost: a child's "
                f"context.page is replaced by the page's shared dict once rendering starts. Put "
                f"the widget's own values in context.data, and page-wide ones in set_context(), "
                f"where context.page is the shared dict.")
        widget.context.page = self.context.page

    def _render_children_to_html(self):
        """Pass 3: replaces each child in `context.children` with its rendered `SafeText`."""
        self._children_rendered = True

        rendered_children = {}

        for key, value in self.context.children.items():
            if value is None:
                rendered_children[key] = None
            elif isinstance(value, list):
                rendered_list = []
                for widget in value:
                    if not isinstance(widget, _Widget):
                        raise TypeError(f"Expected a widget in children['{key}'] list, got {type(widget)}")
                    widget._render_children_to_html()
                    html = widget._render_template()
                    rendered_list.append(html)
                rendered_children[key] = rendered_list
            elif isinstance(value, _Widget):
                widget = value
                widget._render_children_to_html()
                html = widget._render_template()
                rendered_children[key] = html
            else:
                raise TypeError(f"Expected a widget, a list of widgets, or None in children['{key}'], got {type(value)}")

        self.context.children = rendered_children

    def _generate_debug_tree(self, indent: int = 0) -> str:
        """This widget and its descendants as indented HTML lines, labelled by `debug_label`."""
        lines = []

        if self.debug_label is not None:
            display_name = f"{self.__class__.__name__}({str(self.debug_label)})"
        else:
            display_name = self.__class__.__name__
        lines.append(f"<div style='margin-left: {indent * 20}px; color: #000;'>{display_name}</div>")

        for key, value in self.context.children.items():
            if value is None:
                lines.append(f"<div style='margin-left: {(indent + 1) * 20}px; color: #888;'>{key}: <span style='color: #999;'>None</span></div>")
            elif isinstance(value, list):
                lines.append(f"<div style='margin-left: {(indent + 1) * 20}px; color: #888;'>{key}: [</div>")
                for item in value:
                    if isinstance(item, _Widget):
                        lines.append(item._generate_debug_tree(indent + 2))
                lines.append(f"<div style='margin-left: {(indent + 1) * 20}px; color: #888;'>]</div>")
            elif isinstance(value, _Widget):
                lines.append(f"<div style='margin-left: {(indent + 1) * 20}px; color: #888;'>{key}:</div>")
                lines.append(value._generate_debug_tree(indent + 2))

        return "\n".join(lines)

    def get_template_path(self) -> str:
        """
        Return the path to this widget's template file.

        With `template_filename` unset, the template is named after the class's module: a widget
        class defined in `cookie_banner.py` renders `cookie_banner.html` in the same directory.

        `template_filename` must be a bare file name. It is looked up beside the class's own
        file, then beside each base class's file in MRO order, so a base class can keep a
        variant beside its own module and set it for every subclass.

        Override this in subclasses when the choice needs more than an attribute.
        """
        if self.template_filename is None:
            return self._resolve_beside_class_file(self._module_named_template())
        return self._find_beside_class_or_bases(self.template_filename)

    def _find_beside_class_or_bases(self, filename: str) -> str:
        if not filename or filename in ('.', '..') or '/' in filename or '\\' in filename:
            raise ValueError(
                f'{type(self).__name__}.template_filename must be a bare file name, '
                f'not {filename!r}')
        searched = []
        for cls in type(self).__mro__:
            if cls.__module__ in self._LIBRARY_MODULES or not issubclass(cls, _Widget):
                continue
            folder = os.path.dirname(inspect.getfile(cls))
            if folder in searched:
                continue
            searched.append(folder)
            candidate = os.path.join(folder, filename)
            if os.path.isfile(candidate):
                return candidate
        raise FileNotFoundError(
            f'{type(self).__name__}.template_filename {filename!r} is in none of: '
            f'{", ".join(searched)}')

    def _module_named_template(self) -> str:
        class_filename = os.path.basename(inspect.getfile(self.__class__))
        return class_filename.replace('.py', '.html')

    def _resolve_beside_class_file(self, path: str) -> str:
        class_dir = os.path.dirname(inspect.getfile(self.__class__))
        return os.path.join(class_dir, path)

    def _context_dict(self) -> dict:
        context = {}
        # None when rendered without a request.
        context['request'] = self._request
        # No `user` key: `request.user` is whatever the project's middleware set, and Django's
        # default is a lazy object whose first read queries the database, which raises inside an
        # async page. A page that wants the user puts it in `context.page` the way its middleware
        # allows.
        context['page'] = self.context.page
        context['data'] = self.context.data
        context['children'] = self.context.children
        return context

    def _render_template(
        self,
        template_path: str | None = None,
        extra_context: dict | None = None,
    ) -> SafeText:
        """
        Fill this widget's template with the context it already has: no `set_context()`, no
        children rendered. The pipeline calls it once both are done; use `render()` or `arender()`
        to render a widget from outside the pipeline.

        Args:
            template_path: Full path to the template file, for a page's document template. If
                None, uses `get_template_path()`.
            extra_context: Merged over the widget's context, for a page's document template.
        """
        context = self._context_dict()
        if extra_context:
            context.update(extra_context)
        filepath = self.get_template_path() if template_path is None else template_path
        with open(filepath, 'r') as file:
            template = Template(file.read())
        return template.render(Context(context))


class AsyncWidget(_Widget):
    """
    A widget whose `set_context()` is `async def`, so it awaits the ORM's async methods. Renders
    in an `AsyncWebPage` or with `await arender()`; `render()` and a `SyncWebPage` refuse it.
    A `def set_context()` raises when the class is defined.
    """

    _renders_async = True

    async def set_context(self):
        """The widget's data and children. Base implementation does nothing."""
        pass


class SyncWidget(_Widget):
    """
    A widget whose `set_context()` is plain `def`, or that has none. Renders everywhere: in either
    page, with `render()` from sync code (a plain view, an email, the admin) and with `arender()`.
    In an `AsyncWebPage` or `arender()` it runs on the event loop, so its `set_context()` makes no
    database query there. An `async def set_context()` raises when the class is defined.
    """

    _renders_async = False
