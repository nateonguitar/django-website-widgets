# Examples

Small Django projects you can run, each showing one part of django-website-widgets. They're not
part of the package: clone the repository to use them.

```bash
git clone https://github.com/nateonguitar/django-website-widgets.git
cd django-website-widgets/examples/slim/01_pages_and_widgets
poetry install
poetry run python manage.py migrate
poetry run python manage.py runserver
```

Then open http://localhost:8000/. Each project runs the package from this repository, so it always
shows the current code. Each has its own README, and `poetry run python manage.py test` runs its
tests.

## Slim: no build step

These need only Python and [Poetry](https://python-poetry.org/), no Node. Styles are a static CSS
file, the script every page needs is a static JavaScript file, and each widget's own behaviour is
an inline `<script>` in its template. Read them in order.

| Project | Shows |
| --- | --- |
| [`slim/01_pages_and_widgets`](slim/01_pages_and_widgets) | a `Page` and its document template, child widgets, data passed down through constructors, `context.page`, list and `None` children, variant templates, template lookup through base classes, the debug tree, and async `set_context()` with the async ORM, including what a synchronous query does inside a page |
| [`slim/02_requests_and_routing`](slim/02_requests_and_routing) | routing with `@register_url` beside a page routed by hand, `show_page_resolve_order`, `handle_request()` for access variants (401, 403, 404), a redirect and an ETag with a 304, and `arender()` behind a "load more" endpoint |
| [`slim/03_widgets_in_plain_django`](slim/03_widgets_in_plain_django) | no `Page` at all: `render()` in an ordinary `TemplateView`, HTML emails built from a document widget around each email's own content widget, and an admin tool page beside a real `ModelAdmin` |
| [`slim/04_project_tracker`](slim/04_project_tracker) | a small working app using all of it: logins, an appbar and footer, access variants, and creating, editing and deleting through JSON endpoints |

For a real project built on the package, see [Gametabs](https://gametabs.net).
