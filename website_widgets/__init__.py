from .widget import Widget
from .web_page import WebPage
from .widget_context import WidgetContext
from .url_templates import reverse_template
from .page_routes import PageRoutes
from .npm_watch import NpmWatch

register_url = PageRoutes.register_url
start_npm_watch = NpmWatch.start

__all__ = [
    'Widget',
    'WebPage',
    'WidgetContext',
    'reverse_template',
    'PageRoutes',
    'register_url',
    'NpmWatch',
    'start_npm_watch',
]
