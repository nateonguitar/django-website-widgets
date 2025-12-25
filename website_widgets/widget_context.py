from typing import Any


class ContextCollection:
    """
    A collection of context variables for widget rendering.
    """

    def __init__(self, data: dict[str, Any] | None = None):
        self._data: dict[str, Any] = data or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert the collection to a dictionary."""
        return self._data.copy()

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    def __getitem__(self, key: str) -> Any:
        return self._data[key]


class WidgetContext:
    """
    Context for a widget render.

    Three context collections:
    - page: Global page-level variables (shared reference across all widgets, gathered from the root parent page)
    - data: Widget-specific variables (fresh per widget)
    - children: Rendered child widget HTML strings (fresh per widget)
    """

    def __init__(self, parent: 'WidgetContext | None' = None):
        self.data = ContextCollection()
        self.children = ContextCollection()

        if parent is not None:
            self.page = parent.page
        else:
            self.page = ContextCollection()

    def to_dict(self) -> dict[str, Any]:
        """
        Converts the widget context to a flat dictionary for template rendering.
        """
        context = self.data.to_dict()

        for key, value in self.children.to_dict().items():
            context[f'{key}_html'] = value

        return context
