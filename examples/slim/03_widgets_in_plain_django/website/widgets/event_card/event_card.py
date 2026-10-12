from website_widgets import Widget

from website.models import Event


class EventCard(Widget):
    """One event, with a button that shows its description: the widget's own inline script."""

    def __init__(self, event: Event):
        super().__init__()
        self.event = event

    def set_context(self):
        self.context.data['event'] = self.event
