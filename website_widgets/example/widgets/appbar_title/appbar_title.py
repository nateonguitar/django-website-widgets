from website_widgets import Widget


class AppbarTitle(Widget):
    """Title widget for the appbar."""

    def __init__(self, title: str, parent: 'Widget | None' = None):
        super().__init__(parent=parent)
        self.context.data['title'] = title
        self._debug_label = title

    def html(self):
        return self.render_html()
