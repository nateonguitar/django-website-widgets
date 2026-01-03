from website_widgets import Widget


class InfoCard(Widget):
    """
    Example reusable widget demonstrating explicit data passing.
    Data is passed via constructor, then rendered by the system.
    """

    def __init__(self, title: str, content: str, parent: 'Widget | None' = None):
        super().__init__(parent=parent)
        self.context.data['title'] = title
        self.context.data['content'] = content
        self._debug_label = title

    def html(self):
        return self.render_html()
