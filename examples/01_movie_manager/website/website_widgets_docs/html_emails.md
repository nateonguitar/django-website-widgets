# HTML emails

A lesson: an HTML email built from widgets. The email's whole document is one widget, its own
part another, rendered with `render()` and no request. Read this before writing a site's emails.
Why an email is a widget and never a page is in `rendering_pipeline.md`.

## The document widget

Every email shares a document: the `<head>`, a header and a footer. That is an `EmailDocument`
widget whose template is the whole document, taking the one email's own part as a child in its
constructor:

```python
class EmailDocument(SyncWidget):
    def __init__(self, subject: str, site_url: str, content: SyncWidget):
        super().__init__()
        self.subject = subject
        self.site_url = site_url
        self.content = content

    def set_context(self):
        # Before its children run, so the content widget and anything inside it can link back.
        self.context.page['site_url'] = self.site_url
        self.context.data['subject'] = self.subject
        self.context.children['content'] = self.content
```

```django
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <title>{{ data.subject }}</title>
    </head>
    {# Inline styles only: most mail apps drop <style> blocks and linked stylesheets. #}
    <body style="margin: 0; padding: 24px 12px; font-family: Arial, sans-serif;">
        {{ children.content }}
        <p style="font-size: 12px;"><a href="{{ page.site_url }}">Visit the site</a></p>
    </body>
</html>
```

Each email's content is its own widget (`EventReminder(event=event)`, a digest's list of row
widgets), so one email's markup never lives inside another's template. The document is then
`EmailDocument(subject=..., site_url=..., content=EventReminder(event=event)).render()`.

**What every email shares is a widget the document places,** never markup repeated in each
email's content. A company-style footer, the same links and the same "why you got this" line in
every email, is an `EmailFooter` widget that `EmailDocument.set_context()` adds as a child
beside the content; changing it changes every email at once.

## What an email needs that a page doesn't

- **`def set_context()` throughout.** Emails are sent from sync code (a management command, a
  Celery task, a view's `post()`), and `render()` refuses an `async def set_context()`. The sync
  ORM is fine there. `ww_create_widget --sync` writes one.
- **No request.** `render()` without one leaves `self.request` raising and `{{ request }}` empty,
  so nothing can build a URL from the request's host.
- **Absolute links.** An email has no host to be relative to, so every link is the site's base
  URL plus a path: `f'{site_url}{reverse("upcoming_events")}'`, handed down through
  `context.page` as above. `{% url %}` alone writes a relative path that goes nowhere in a mail
  app.
- **A plain-text version beside the HTML,** for mail apps that don't show HTML. It's written by
  hand rather than stripped from the HTML, since a link has to read as a full URL:

```python
from django.core.mail import EmailMultiAlternatives

message = EmailMultiAlternatives(subject=subject, body=text_body, to=[to])
message.attach_alternative(document.render(), 'text/html')
message.send()
```

A class per email (`EventReminderEmail`, with its subject, plain-text body and content widget)
keeps each email's three parts together; a shared base class can build the document and send it.

## Worked example

The movie manager example sends two emails built this way, a checkout receipt and a return
receipt, both ending in one `EmailFooter`:
[`examples/01_movie_manager/website/widgets/emails/`](https://github.com/nateonguitar/django-website-widgets/tree/main/examples/01_movie_manager/website/widgets/emails)
holds the widgets and
[`website/emails/`](https://github.com/nateonguitar/django-website-widgets/tree/main/examples/01_movie_manager/website/emails)
the email classes. Its API endpoints are async, so each sends through `sync_to_async`, and its
settings print emails to the console instead of sending them.
