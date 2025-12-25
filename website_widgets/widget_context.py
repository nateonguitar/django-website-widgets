from typing import Any


class ContextCollection:
    """
    A collection of context variables for widget rendering.
    """

    def __init__(self, data: dict[str, Any] | None = None):
        self._data: dict[str, Any] = data or {}

    def set(self, key: str, value: Any) -> None:
        """Set a value in the collection."""
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the collection."""
        return self._data.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        """Convert the collection to a dictionary."""
        return self._data.copy()

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]


class WidgetContext:
    """
    Context for a widget render.

    Three context collections:
    - data: Widget-specific variables (fresh per widget, no parent inheritance)
    - children: Rendered child widget HTML strings (fresh per widget)
    - page: Global page-level variables (shared reference across all widgets)
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
