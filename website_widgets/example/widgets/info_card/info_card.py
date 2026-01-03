from website_widgets import Widget


class InfoCard(Widget):
    """
    Example reusable widget demonstrating explicit data passing.
    Data is passed via constructor, then rendered by the system.
    """

    def __init__(self, title: str, content: str):
        super().__init__()
        self.title = title
        self.content = content
        self._debug_label = title

    def set_context(self):
        self.context.data['title'] = self.title
        self.context.data['content'] = self.content
