from .widget import Widget
from .page import Page
from .widget_context import WidgetContext
from .url_templates import reverse_template
from .page_routes import PageRoutes

register_url = PageRoutes.register_url

__all__ = [
    'Widget',
    'Page',
    'WidgetContext',
    'reverse_template',
    'PageRoutes',
    'register_url',
]
