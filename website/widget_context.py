# Backward-compatible re-export from new location
# TODO: Update all imports to use website_widgets.widget_context directly
from website_widgets.widget_context import ContextCollection, WidgetContext

__all__ = ['ContextCollection', 'WidgetContext']
