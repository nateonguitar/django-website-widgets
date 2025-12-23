from __future__ import annotations
from django.conf import settings
from django.http import HttpRequest
from django.template import Template, Context
from django.utils.safestring import mark_safe, SafeText
import os
from website.widget_context import WidgetContext

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
        return mark_safe(f'({self.__class__.__name__})')

    def html_sync(self) -> SafeText:
        return mark_safe(f'({self.__class__.__name__})')

    def render_html(
            self,
            template_path: str,
            context: dict = {}) -> SafeText:
        context['request'] = self.request
        context['data'] = self.context.data.to_dict()
        context['children'] = self.context.children.to_dict()
        context['user'] = self.request.user
        context['page'] = self.context.page.to_dict()
        filepath = os.path.join(settings.BASE_DIR, template_path)
        with open(filepath, 'r') as file:
            template = Template(file.read())
        return template.render(Context(context))
