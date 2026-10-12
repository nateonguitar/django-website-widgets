from website_widgets import Widget

from website.emails.email import Email
from website.models import Event
from website.widgets.event_digest.event_digest import EventDigest


class EventDigestEmail(Email):
    """Every upcoming event, as an `EventDigest` inside the shared document."""

    def __init__(self, events: list[Event], site_url: str):
        super().__init__(site_url=site_url)
        self.events = events

    def get_subject(self) -> str:
        return 'Upcoming events'

    def get_text_body(self) -> str:
        lines = [
            f'{event.name}, {event.starts_at:%a %d %b %Y}: {self.get_event_url(event)}'
            for event in self.events
        ]
        return '\n'.join(lines)

    def build_content(self) -> Widget:
        return EventDigest(events=self.events)
