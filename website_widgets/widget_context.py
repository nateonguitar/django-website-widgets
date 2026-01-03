from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from website_widgets.widget import Widget

class WidgetContext:
    """
    Context for a widget render.

    Three context collections:
    - page: Global page-level variables (shared reference across all widgets, gathered from the root parent page)
    - data: Widget-specific variables (fresh per widget)
    - children: Child widgets to be rendered (Widget instances or lists of Widget instances)
    """

    def __init__(self, parent: 'WidgetContext | None' = None):
        self.page = parent.page if parent is not None else {}
        self.data = {}
        self.children: dict[str, 'Widget | list[Widget]'] = {}
