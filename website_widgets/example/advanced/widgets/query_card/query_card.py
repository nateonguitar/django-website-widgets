from website_widgets import Widget


class QueryCard(Widget):
    """Shows when one mock query started and finished, given to it by its parent."""

    def __init__(self, label: str, started_ms: int | None = None, finished_ms: int | None = None):
        super().__init__()
        self.label = label
        self.started_ms = started_ms
        self.finished_ms = finished_ms

    def set_context(self):
        self.context.data['label'] = self.label
        self.context.data['started_ms'] = self.started_ms
        self.context.data['finished_ms'] = self.finished_ms
