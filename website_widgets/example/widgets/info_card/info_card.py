from website_widgets import Widget


class InfoCard(Widget):
    """
    Example reusable widget demonstrating explicit data passing.
    All data comes via html_sync() parameters, not from parent context.
    """

    def html_sync(self, title: str, content: str):
        self.context.data['title'] = title
        self.context.data['content'] = content
        return self.render_html()
