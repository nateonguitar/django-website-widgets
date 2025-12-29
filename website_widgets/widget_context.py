from typing import Any

class WidgetContext:
    """
    Context for a widget render.

    Three context collections:
    - page: Global page-level variables (shared reference across all widgets, gathered from the root parent page)
    - data: Widget-specific variables (fresh per widget)
    - children: Rendered child widget HTML strings (fresh per widget)
    """

    def __init__(self, parent: 'WidgetContext | None' = None):
        self.page = parent.page if parent is not None else {}
        self.data = {}
        self.children = {}
