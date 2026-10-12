from website_widgets import Widget

from website.models import Event


class EventReminder(Widget):
    """The reminder email's own part: one event's details and a link to its card."""

    def __init__(self, event: Event):
        super().__init__()
        self.event = event

    def set_context(self):
        self.context.data['event'] = self.event
