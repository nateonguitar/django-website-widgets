from django.views.generic import TemplateView

from website.widgets.event_list.event_list import EventList


class UpcomingEventsView(TemplateView):
    """
    An ordinary Django view and template, `{% extends %}` and context processors included, holding
    widget HTML: how a site that already exists adopts widgets without converting a view to a
    `WebPage`. `render()` returns `SafeText`, so the template outputs it unescaped.
    """

    template_name = 'website/upcoming_events.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event_list_html'] = EventList().render(self.request)
        return context
