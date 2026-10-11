from __future__ import annotations
import inspect
from django.apps import apps
from django.conf import settings
from django.http import HttpRequest
from django.template import Template, Context
from django.utils.safestring import SafeText
import os
from website_widgets.widget_context import WidgetContext

class Widget:
    template_filename: str | None = None
    # Shown beside the class name in the debug tree, to tell instances apart.
    _debug_label: object | None = None
    # Library base classes, whose folders hold no application templates.
    _LIBRARY_MODULES = ('website_widgets.widget', 'website_widgets.page')

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

        Access the user via `self.request.user`. For custom user models with
        additional fields or methods, type hint locally for IDE support:

        ```python
        from api.models import User
        request_user: User = self.request.user
        request_user.custom_method()
        ```
        """
        if self._request is not None:
            return self._request
        raise RuntimeError(
            f'{type(self).__name__} has no request: it gets one from the page rendering it, or '
            f'from the request passed to render() or arender().')

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

        Use `def` for sync, `async def` for async - system auto-detects. A widget rendered with
        `render()` must use `def`. Base implementation does nothing.
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
        on a widget whose `set_context()` is `async def`; await `arender()` for those. Values put
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
                f'{type(self).__name__}.set_context() is async, so render() cannot run it; '
                f'await arender() instead, or write set_context() with def.')
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

    def _child_widgets(self) -> list[Widget]:
        widgets = []
        for key, value in self.context.children.items():
            if isinstance(value, list):
                for widget in value:
                    if not isinstance(widget, Widget):
                        raise TypeError(f"Expected Widget in children['{key}'] list, got {type(widget)}")
                    widgets.append(widget)
            elif isinstance(value, Widget):
                widgets.append(value)
        return widgets

    def _share_render_state_with(self, widget: Widget):
        # Request and page context are shared by reference across the whole tree.
        widget._request = self._request
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
                    if not isinstance(widget, Widget):
                        raise TypeError(f"Expected Widget in children['{key}'] list, got {type(widget)}")
                    widget._render_children_to_html()
                    html = widget._render_template()
                    rendered_list.append(html)
                rendered_children[key] = rendered_list
            elif isinstance(value, Widget):
                widget = value
                widget._render_children_to_html()
                html = widget._render_template()
                rendered_children[key] = html
            else:
                raise TypeError(f"Expected Widget, list[Widget], or None in children['{key}'], got {type(value)}")

        self.context.children = rendered_children

    def _generate_debug_tree(self, indent: int = 0) -> str:
        """This widget and its descendants as indented HTML lines, labelled by `_debug_label`."""
        lines = []

        if self._debug_label is not None:
            display_name = f"{self.__class__.__name__}({str(self._debug_label)})"
        else:
            display_name = self.__class__.__name__
        lines.append(f"<div style='margin-left: {indent * 20}px; color: #000;'>{display_name}</div>")

        for key, value in self.context.children.items():
            if value is None:
                lines.append(f"<div style='margin-left: {(indent + 1) * 20}px; color: #888;'>{key}: <span style='color: #999;'>None</span></div>")
            elif isinstance(value, list):
                lines.append(f"<div style='margin-left: {(indent + 1) * 20}px; color: #888;'>{key}: [</div>")
                for item in value:
                    if isinstance(item, Widget):
                        lines.append(item._generate_debug_tree(indent + 2))
                lines.append(f"<div style='margin-left: {(indent + 1) * 20}px; color: #888;'>]</div>")
            elif isinstance(value, Widget):
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
            if cls.__module__ in self._LIBRARY_MODULES or not issubclass(cls, Widget):
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
        # Also None without django.contrib.auth.
        context['user'] = getattr(self._request, 'user', None)
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
