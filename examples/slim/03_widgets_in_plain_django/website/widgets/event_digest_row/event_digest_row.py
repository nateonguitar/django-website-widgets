from website_widgets import Widget

from website.models import Event


class EventDigestRow(Widget):
    """One event in the digest email, linked by an absolute URL, since an email has no host."""

    def __init__(self, event: Event):
        super().__init__()
        self.event = event

    def set_context(self):
        self.context.data['event'] = self.event
