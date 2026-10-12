from website_widgets import Widget

from website.models import Event
from website.widgets.event_digest_row.event_digest_row import EventDigestRow


class EventDigest(Widget):
    """The digest email's own part: every upcoming event, one row widget each."""

    def __init__(self, events: list[Event]):
        super().__init__()
        self.events = events

    def set_context(self):
        self.context.data['event_count'] = len(self.events)
        self.context.children['rows'] = [EventDigestRow(event=event) for event in self.events]
