# Pages and widgets

How a page is built: a `WebPage` and its document template, child widgets, how data reaches them,
variant templates, and loading data in `async def set_context()`.

```bash
poetry install
poetry run python manage.py migrate
poetry run python manage.py runserver
```

Then open http://localhost:8000/. Set `SHOW_DEBUG_TREE=1` before `runserver` to see each page's
widget tree drawn under it. Tests: `poetry run python manage.py test`.

| Page | Shows |
| --- | --- |
| `/composition/` | constructor data, a list of children, a `None` child, the shared `context.page` |
| `/async/` | the async ORM, a synchronous query failing inside a page, slow calls gathered by a parent or awaited one after another, a template found beside a base class |
| `/books/<id>/` | a variant template, `book_page__not_found.html`, with a 404 |

- `website/pages/example_page.py` is the base page every page extends. It has no `@register_url`,
  so it isn't routed; `document_template.html` beside it is the shared document.
- `website/static/website/` holds `styles.css` and `analytics.js`, which the document template
  loads for every page. A widget's own behaviour would be an inline `<script>` in its template.
- `website/migrations/0002_seed_books.py` seeds the books, so `migrate` gives a full shelf.
