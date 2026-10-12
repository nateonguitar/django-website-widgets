# Widgets in plain Django

No `Page` at all: widgets rendered with `render()` into an ordinary `TemplateView` whose
template uses `{% extends %}`, HTML emails with no request, and a custom admin page beside a real
`ModelAdmin`. This is how an existing Django site adopts widgets one piece at a time.

```bash
poetry install
poetry run python manage.py migrate
poetry run python manage.py runserver
```

Then open http://localhost:8000/. The admin is at http://localhost:8000/admin/; log in as `admin`,
password `try-the-widgets`. To see the emails, which are printed to the console rather than sent:

```bash
poetry run python manage.py send_event_digest --to you@example.com
poetry run python manage.py send_event_reminder --to you@example.com
```

Tests: `poetry run python manage.py test`.

- `website/views/upcoming_events_view.py` renders an `EventList` widget into a plain template.
  `render()` runs no event loop, so the widget's `def set_context()` uses the sync ORM, the reverse
  of a page, where that query would raise `SynchronousOnlyOperation`.
- `website/widgets/email_document/` is `EmailDocument`, a widget whose template is a whole HTML
  document: the `<head>`, header and footer every email shares, around a `content` widget passed
  to its constructor. A widget's template can be a whole document, so an email needs no `Page`.
- `website/emails/` holds each email as a plain class on `Email`, which renders the document
  with `render()` and no request and sends it beside a plain-text version. `EventDigestEmail`'s
  content is `EventDigest`, a list of row widgets; `EventReminderEmail`'s is `EventReminder`,
  one event.
- `website/example_admin_site.py` adds the tool page through the admin site's `get_urls()`, beside
  the `Event` admin. Its view is a plain admin view, since the admin's templates need
  `admin_site.each_context()`.
- Each event card keeps its own "Show details" script inline, beside its markup; the analytics
  script every page needs is a static file the base template loads.
