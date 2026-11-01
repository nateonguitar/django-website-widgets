from .widget import Widget
from .web_page import AsyncWebPage, SyncWebPage
from .widget_context import WidgetContext
from .url_templates import reverse_template
from .page_routes import PageRoutes
from .npm_watch import NpmWatch

register_url = PageRoutes.register_url
start_npm_watch = NpmWatch.start

__all__ = [
    'Widget',
    'AsyncWebPage',
    'SyncWebPage',
    'WidgetContext',
    'reverse_template',
    'PageRoutes',
    'register_url',
    'start_npm_watch',
]
