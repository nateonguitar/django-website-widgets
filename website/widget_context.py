from typing import Any


class ContextCollection:
    """
    A collection of context variables that can be inherited from a parent.
    """

    def __init__(self, data: dict[str, Any] | None = None):
        self._data: dict[str, Any] = data or {}

    @classmethod
    def from_collection(cls, collection: 'ContextCollection') -> 'ContextCollection':
        """
        Creates a new ContextCollection by copying data from a parent collection.
        Used for patching parent data with child-specific values.
        """
        return cls(data=collection._data.copy())

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
    - data: Patches parent context with widget-specific variables
    - children: Fresh collection for child widgets (no parent pollution)

    Constructor "parent" argument is WidgetContext | None
    """

    def __init__(self, parent = None):
        # data patches from parent
        if parent is not None:
            p: WidgetContext = parent
            self.data = ContextCollection.from_collection(p.data)
            self.page = p.page
        else:
            self.data = ContextCollection()
            self.page = ContextCollection()

        # children always starts fresh
        self.children = ContextCollection()

    def to_dict(self) -> dict[str, Any]:
        """
        Converts the widget context to a flat dictionary for template rendering.
        Combines data and renders children as HTML strings.
        """
        context = self.data.to_dict()

        # Add children as rendered HTML (assuming they're widgets)
        for key, value in self.children.to_dict().items():
            context[f'{key}_html'] = value

        return context
