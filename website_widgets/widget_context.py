from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from website_widgets.widget import _Widget

class WidgetContext:
    """
    Context for a widget render.

    Three context collections:
    - page: Global page-level variables, one dict shared by every widget in the tree: the render
      pipeline gives each child its parent's before the child's set_context() runs
    - data: Widget-specific variables (fresh per widget)
    - children: Child widgets to be rendered (AsyncWidget or SyncWidget instances, or lists of them)
    """

    def __init__(self):
        self.page = {}
        self.data = {}
        self.children: dict[str, '_Widget | list[_Widget]'] = {}
