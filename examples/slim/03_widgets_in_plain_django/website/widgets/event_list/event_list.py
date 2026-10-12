from django.utils import timezone

from website_widgets import Widget

from website.models import Event
from website.widgets.event_card.event_card import EventCard


class EventList(Widget):
    """
    Every upcoming event, one `EventCard` each. Queries in a plain `def set_context()` with the
    sync ORM, which is safe only because it's rendered with `render()` from sync code: inside a
    page's async pipeline the same query would raise `SynchronousOnlyOperation`.
    """

    def set_context(self):
        upcoming = Event.objects.filter(starts_at__gte=timezone.now())
        self.context.children['cards'] = [EventCard(event=event) for event in upcoming]
