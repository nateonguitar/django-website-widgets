from __future__ import annotations
import inspect
from django.conf import settings
from django.http import HttpRequest
from django.template import Template, Context
from django.utils.safestring import SafeText
import os
from website_widgets.widget_context import WidgetContext

class Widget:
    def __init__(self, parent: 'Widget | None' = None):
        self.parent = parent
        self._request: HttpRequest | None = parent._request if parent else None
        self.context = WidgetContext(
            parent=parent.context if parent else None)

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

    async def html(self) -> SafeText:
        return self.render_html()

    def html_sync(self) -> SafeText:
        return self.render_html()

    def template_path(self) -> str:
        """
        Return the path to this widget's template.html file.
        Auto-detected from the subclass file location. Override if needed.

        Override this in subclasses if the template is not in the same folder
        as the widget class file.
        """
        return os.path.join(os.path.dirname(inspect.getfile(self.__class__)), 'template.html')

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
                `template.html` in the same directory as the widget class file,
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
