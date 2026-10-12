from django.urls import reverse

from website_widgets import Widget

from website.models import Event


class EventsTable(Widget):
    """Every event as a table styled by the admin's own stylesheet, linking each to its change page."""

    def set_context(self):
        self.context.data['rows'] = [
            {
                'event': event,
                'change_url': reverse('admin:website_event_change', args=[event.pk]),
            }
            for event in Event.objects.all()
        ]
