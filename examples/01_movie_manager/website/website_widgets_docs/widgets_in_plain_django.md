# Widgets in plain Django

A lesson: widgets used without a page class, in an ordinary Django view and template, and in a
custom admin page. This is how a site that already exists adopts widgets one piece at a time.
Read this before putting a widget into a view that isn't a page. `rendering_a_widget_alone.md` explains
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
`SynchronousOnlyOperation`. Such a widget is a `SyncWidget`; `render()` refuses an `AsyncWidget`
with a message naming it. `ww_create_widget --sync` writes one (`creating_pages_and_widgets.md`).

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

A tool page beside the model admins is a plain admin view, not a page class: the admin's templates
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

## A widget as a form field

A widget can be a working form field, in a Django form and so in the admin, through a small
`forms.Widget` subclass whose `render()` returns the widget's:

```python
class RatingSelect(forms.Select):
    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        picker = RatingPicker(name=name, value=value or '', select_id=attrs.get('id'))
        return picker.render()
```

The widget's template writes an input with the field's `name`, so Django's own
`value_from_datadict()` still reads what's submitted, and passing the form's `id` on keeps
`<label for>` pointing at it. A `ModelForm`'s `Meta.widgets = {'rating': RatingSelect()}` puts it
in the admin through `ModelAdmin.form`, and the site's own pages can place the same widget as a
child.

**Its controller runs in the admin as on the site.** The widget's own
`<script type="module">` imports `App` and its controller from `{% static "main.js" %}`, so the
admin page loads the bundle with no `Media` or template change; importing it starts nothing
else. Three things differ there:

- **The bundle has to be built and served** wherever the admin is. Rendering the field's
  current state on the server (the chosen option, its description) keeps the field correct and
  submittable even where it isn't, with only the live behavior missing.
- **The site's stylesheet isn't loaded, and shouldn't be,** since its rules would restyle the
  whole admin. The widget's markup leans on the admin's own form styles, plus inline styles for
  anything of its own.
- **Nothing fills the site's state classes,** such as the starter's `AppUrls` and `AppState`,
  which only the site's document template sets. A controller meant for the admin reads only its
  own root's `data-` attributes.

**A widget only the admin uses can be vanilla JavaScript in its own template** instead, the way
the admin's own widgets are, so it works with no build at all. A classic `<script>` (not a
module) finds its own root with `document.currentScript.previousElementSibling`, so several on
one page each find theirs with no id. Keep that for small, self-contained behavior; a widget the
site uses too, or anything bigger, is a `Controller` in the bundle.

**Worked example:** the movie manager example's `MovieAdmin.where_each_copy_is`
([`api/admin/movie_admin.py`](https://github.com/nateonguitar/django-website-widgets/blob/main/examples/01_movie_manager/api/admin/movie_admin.py))
renders the movie page's own `CopyTable` widget into the change page that way. The page and the
admin each load the copies their own way, the page with the async ORM and the admin with the sync
one, and hand them to the widget's constructor, so one template serves both. Its `RatingPicker`
([`website/widgets/rating_picker/`](https://github.com/nateonguitar/django-website-widgets/tree/main/examples/01_movie_manager/website/widgets/rating_picker))
is the form-field case: the Movie admin's rating field through `RatingSelect`, and the
add-to-inventory page's, with one `RatingPickerController` showing what each rating means in both.
Its `ReturnRentalField`
([`api/admin/widgets/return_rental_field/`](https://github.com/nateonguitar/django-website-widgets/tree/main/examples/01_movie_manager/api/admin/widgets/return_rental_field))
is the admin-only case: the Rental admin's "Returned" field, with a Return button whose vanilla
JavaScript calls the site's own return endpoint, sending the CSRF token the change form already
carries, since the cookie is HttpOnly. It nests the site's own `Timestamp` widget for its dates,
so composition works across the line too: an admin-only widget's children can be the site's.
