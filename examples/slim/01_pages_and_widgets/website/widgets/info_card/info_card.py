from website_widgets import Widget


class InfoCard(Widget):
    """A titled card, given everything it shows through its constructor."""

    def __init__(self, title: str, body: str):
        super().__init__()
        self.title = title
        self.body = body
        # Tells the cards apart in the debug tree: `InfoCard(List child 2)`.
        self._debug_label = title

    def set_context(self):
        self.context.data['title'] = self.title
        self.context.data['body'] = self.body
