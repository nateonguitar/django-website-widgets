from website_widgets import Widget

from website.emails.email import Email
from website.models import Event
from website.widgets.event_reminder.event_reminder import EventReminder


class EventReminderEmail(Email):
    """One event that's coming up, as an `EventReminder` inside the same document as the digest."""

    def __init__(self, event: Event, site_url: str):
        super().__init__(site_url=site_url)
        self.event = event

    def get_subject(self) -> str:
        return f'Coming up: {self.event.name}'

    def get_text_body(self) -> str:
        lines = [
            self.event.name,
            f'{self.event.starts_at:%a %d %b %Y, %H:%M} at {self.event.location}',
        ]
        if self.event.description:
            lines.append(self.event.description)
        lines.append(self.get_event_url(self.event))
        return '\n'.join(lines)

    def build_content(self) -> Widget:
        return EventReminder(event=self.event)
