# ETags and 304 Not Modified

A lesson: a page answering 304 Not Modified when the browser already holds its current version,
before any widget is built. Read this before adding conditional responses or caching headers to a
page. Overriding `handle_request()` is covered in `rendering_pipeline.md`; this is one use of it.

## Answering before the tree is built

`handle_request()` runs before any `set_context()`, so a page can compare the browser's
`If-None-Match` with a cheap fingerprint of what it would render, and skip the whole tree when
they match:

```python
from django.db.models import Count, Max
from django.http import HttpResponseNotModified
from django.utils.http import parse_etags

@register_url('changelog/', name='changelog')
class ChangelogPage(AppPage):
    async def handle_request(self, request, *args, **kwargs):
        etag = await self._etag(request)
        if etag in parse_etags(request.headers.get('If-None-Match', '')):
            response = HttpResponseNotModified()
        else:
            response = await super().handle_request(request, *args, **kwargs)
        response['ETag'] = etag
        # The browser keeps the page but asks every time, so a change shows at once.
        response['Cache-Control'] = 'no-cache'
        response['Vary'] = 'Cookie'
        return response

    @staticmethod
    async def _etag(request) -> str:
        summary = await Article.objects.aaggregate(count=Count('id'), newest=Max('updated_at'))
        newest_stamp = int(summary['newest'].timestamp()) if summary['newest'] else 0
        viewer = await request.auser()
        return f'"articles-{summary["count"]}-{newest_stamp}-viewer-{viewer.pk or 0}"'
```

## What goes in the ETag

**Everything that changes the HTML, and nothing else.** Here that's the articles, through their
count (so a deletion changes it) and the newest `updated_at` (an `auto_now` field, so an edit
does), and the viewer, because the page shows who is signed in. Leave one out and a visitor keeps
a stale page; put in something that changes on every request and the 304 never happens.

**Anything random or per-render in the markup defeats it** when the ETag is computed from the
HTML itself: an id from `uuid4()` or `id(self)`, a timestamp, a CSRF token. Building the ETag from
the data, as above, avoids that, and costs one aggregate query instead of the whole page.

**`Vary: Cookie` when the viewer is in it,** so a shared cache never hands one person's page to
another. A page that looks the same to everyone leaves the viewer and the header out.
