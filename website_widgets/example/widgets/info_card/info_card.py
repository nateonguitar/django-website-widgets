from website_widgets import Widget


class InfoCard(Widget):
    """
    Example reusable widget demonstrating explicit data passing.
    All data comes via html_sync() parameters, not from parent context.
    """

    def html_sync(self, title: str, content: str):
        self.context.data.set('title', title)
        self.context.data.set('content', content)
        return self.render_html(self.template_path())
