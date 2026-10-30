# Widgets in plain Django

A lesson: widgets used without a `WebPage`, in an ordinary Django view and template, and in a
custom admin page. This is how a site that already exists adopts widgets one piece at a time.
Read this before putting a widget into a view that isn't a page. `rendering_pipeline.md` explains
`render()` itself; this shows where it fits.

## A widget in an ordinary view

`render()` returns `SafeText`, so its HTML drops into any Django template unescaped. The view
stays a normal Django view, its template keeps `{% extends %}` and context processors, and only
the part that is a widget is rendered by one:

```python
from django.views.generic import TemplateView

class UpcomingEventsView(TemplateView):
    template_name = 'website/upcoming_events.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event_list_html'] = EventList().render(self.request)
        return context
```

```django
{% extends 'website/base.html' %}
{% block content %}
    {{ event_list_html }}
{% endblock %}
```

**A widget rendered this way is written with `def set_context()`,** which is where the sync ORM
belongs here: `render()` runs from sync code with no event loop, so
`Event.objects.filter(...)` works, the reverse of a page, where the same query raises
`SynchronousOnlyOperation`. `render()` refuses an `async def set_context()` with a message
naming the widget. `ww_create_widget --sync` writes one, and a project rendering most of its
widgets this way sets `GenerateComponentConfig(widget_set_context='sync')`
(`creating_pages_and_widgets.md`).

The request is optional. `render(self.request)` lets the widget read `self.request` and its
template `{{ request }}`; without one, `self.request` raises rather than handing it a fake one.

## A widget with a controller, in a plain template

A widget's template starts its own controller from its `<script type="module">`, importing it
from the bundle with `{% static "main.js" %}`, so nothing about the view needs to change for that.
What a page's document template normally does, the plain template does itself:

- **Link the bundled stylesheet** in its `<head>`:
  `<link rel="stylesheet" href="{% static 'bundled-styles.css' %}">`.
- **Fill what controllers read before they start.** A controller reading `AppUrls` needs the URLs
  widget's assignments on the page first; it is a widget like any other, so the view renders it
  too (`context['app_urls_html'] = AppUrls().render(self.request)`) and the template places it
  above the widget. The same goes for a project's `AppState` script.

## A custom admin page

A tool page beside the model admins is a plain admin view, not a `WebPage`: the admin's templates
need `admin_site.each_context()`, and a widget template sees only its four keys. The admin site
adds the view through `get_urls()`, and the view renders the widget into the admin's template:

```python
class ExampleAdminSite(admin.AdminSite):
    def get_urls(self):
        tool_view = EventsAdminToolView.as_view(admin_site=self)
        return [
            path('tools/events/', self.admin_view(tool_view), name='events_tool'),
        ] + super().get_urls()


class EventsAdminToolView(TemplateView):
    template_name = 'admin/website/events_tool.html'
    admin_site = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.admin_site.each_context(self.request))
        context['title'] = 'Events at a glance'
        context['table_html'] = EventsTable().render(self.request)
        return context
```

`events_tool.html` extends `admin/base_site.html` and outputs `{{ table_html }}` in its
`content` block, so the widget is styled by the admin's own stylesheet. `self.admin_view()` keeps
the page behind the admin's login. The same widget renders from a `ModelAdmin`'s
`@admin.display` method, which returns its `render()` output for a change page's read-only field.
