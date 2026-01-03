from website_widgets import Widget


class AppbarTitle(Widget):
    """Title widget for the appbar."""

    def __init__(self, title: str):
        super().__init__()
        self.title = title
        self._debug_label = title

    def set_context(self):
        self.context.data['title'] = self.title
