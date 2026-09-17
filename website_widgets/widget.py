from __future__ import annotations
import inspect
from django.conf import settings
from django.http import HttpRequest
from django.template import Template, Context
from django.utils.safestring import SafeText
import os
from website_widgets.widget_context import WidgetContext

class Widget:
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
        self.context = WidgetContext()

    @property
    def request(self) -> HttpRequest:
        """
        The HttpRequest object for the current page render.
        Cached from parent during construction to avoid tree traversal.

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
        raise RuntimeError("No request found in widget. AppPage should set _request on root before creating children.")

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

        Use `def` for sync, `async def` for async - system auto-detects.
        Base implementation does nothing.
        """
        pass

    async def _initialize_widget_tree(self):
        """
        Traverse the widget tree and call set_context() on all children.
        This happens BEFORE any rendering, ensuring the entire widget tree
        is fully constructed with all data loaded before we render anything.
        """
        for key, value in self.context.children.items():
            if value is None:
                continue
            elif isinstance(value, list):
                for widget in value:
                    if not isinstance(widget, Widget):
                        raise TypeError(f"Expected Widget in children['{key}'] list, got {type(widget)}")

                    # Set request and page context (shared by reference)
                    widget._request = self._request
                    widget.context.page = self.context.page

                    # Call set_context lifecycle hook
                    if inspect.iscoroutinefunction(widget.set_context):
                        await widget.set_context()
                    else:
                        widget.set_context()

                    # Recursively initialize this widget's children
                    await widget._initialize_widget_tree()

            elif isinstance(value, Widget):
                widget = value

                # Set request and page context (shared by reference)
                widget._request = self._request
                widget.context.page = self.context.page

                # Call set_context lifecycle hook
                if inspect.iscoroutinefunction(widget.set_context):
                    await widget.set_context()
                else:
                    widget.set_context()

                # Recursively initialize this widget's children
                await widget._initialize_widget_tree()

    async def _render_children_to_html(self):
        """
        Traverse the widget tree and render all children to HTML.
        Converts self.context.children from Widget objects to SafeText HTML.
        """
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

                    # Recursively render this widget's children first
                    await widget._render_children_to_html()

                    # Then render this widget
                    html = widget.render_html()
                    rendered_list.append(html)

                rendered_children[key] = rendered_list
            elif isinstance(value, Widget):
                widget = value

                # Recursively render this widget's children first
                await widget._render_children_to_html()

                # Then render this widget
                html = widget.render_html()

                rendered_children[key] = html
            else:
                raise TypeError(f"Expected Widget, list[Widget], or None in children['{key}'], got {type(value)}")

        # Replace widget objects with rendered HTML
        self.context.children = rendered_children

    def _generate_debug_tree(self, indent: int = 0) -> str:
        """
        Generate a debug tree visualization of the widget hierarchy.
        Shows widget class names and their children structure with proper indentation.

        Args:
            indent: Current indentation level (0 = root, 1 = first child, etc.)

        Returns:
            HTML string representing this widget and its children
        """
        lines = []

        # Show this widget's name with debug label if available
        debug_label = getattr(self, '_debug_label', None)
        if debug_label is not None:
            display_name = f"{self.__class__.__name__}({str(debug_label)})"
        else:
            display_name = self.__class__.__name__
        lines.append(f"<div style='margin-left: {indent * 20}px; color: #000;'>{display_name}</div>")

        # Show each child
        for key, value in self.context.children.items():
            if value is None:
                # Show None explicitly
                lines.append(f"<div style='margin-left: {(indent + 1) * 20}px; color: #888;'>{key}: <span style='color: #999;'>None</span></div>")

            elif isinstance(value, list):
                # Show list opening
                lines.append(f"<div style='margin-left: {(indent + 1) * 20}px; color: #888;'>{key}: [</div>")

                # Show each item in the list (indented one more level)
                for item in value:
                    if isinstance(item, Widget):
                        lines.append(item._generate_debug_tree(indent + 2))

                # Show list closing
                lines.append(f"<div style='margin-left: {(indent + 1) * 20}px; color: #888;'>]</div>")

            elif isinstance(value, Widget):
                # Show key name
                lines.append(f"<div style='margin-left: {(indent + 1) * 20}px; color: #888;'>{key}:</div>")

                # Show the widget (indented one more level)
                lines.append(value._generate_debug_tree(indent + 2))

        return "\n".join(lines)

    def template_path(self) -> str:
        """
        Return the path to this widget's template file.
        Auto-detected from the subclass Python filename. Override if needed.

        For example, if the widget class is defined in `cookie_banner.py`,
        this will look for `cookie_banner.html` in the same directory.

        Override this in subclasses if the template is not in the same folder
        as the widget class file or uses a different naming convention.
        """
        class_file = inspect.getfile(self.__class__)
        class_dir = os.path.dirname(class_file)
        class_filename = os.path.basename(class_file)
        template_name = class_filename.replace('.py', '.html')
        return os.path.join(class_dir, template_name)

    def _context_dict(self) -> dict:
        context = {}
        context['request'] = self.request
        context['user'] = self.request.user
        context['page'] = self.context.page
        context['data'] = self.context.data
        context['children'] = self.context.children
        return context

    def render_html(
        self,
        template_path: str | None = None,
        extra_context: dict | None = None,
    ) -> SafeText:
        """
        Render this widget to HTML using its template and context.
        Args:
            template_path: Optional path to the template file. If None, uses
                the default `template_path()` method. The default method looks for
                `<module>.html` beside the widget class's `<module>.py`,
                so override that method if the template is elsewhere.
            extra_context: Optional additional context dictionary to merge
                into the widget's context for rendering. Developers should add context
                to `self.context.data` instead of using this. This is used internally
                in the library, not meant for general use.
        """
        context = self._context_dict()
        if extra_context:
            context.update(extra_context)
        filepath = self.template_path() if template_path is None else template_path
        with open(filepath, 'r') as file:
            template = Template(file.read())
        return template.render(Context(context))
