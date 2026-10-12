from django.contrib.admin import AdminSite
from django.views.generic import TemplateView

from website.widgets.events_table.events_table import EventsTable


class EventsAdminToolView(TemplateView):
    """
    A custom admin page holding a widget's HTML. It is a plain view rather than a `Page`, because
    the admin's templates need `admin_site.each_context()` and a page's template sees only its
    five keys.
    """

    template_name = 'admin/website/events_tool.html'
    # Given by the admin site that routes this view.
    admin_site: AdminSite | None = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.admin_site.each_context(self.request))
        context['title'] = 'Events at a glance'
        context['table_html'] = EventsTable().render(self.request)
        return context
