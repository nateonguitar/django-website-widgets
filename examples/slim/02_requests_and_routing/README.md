# Requests and routing

How a request reaches a page, and the ways a page can answer: routes declared with
`@register_url` beside a page routed by hand, and `handle_request()` used for access variants, a
redirect and a 304.

```bash
poetry install
poetry run python manage.py migrate
poetry run python manage.py runserver
```

Then open http://localhost:8000/. Log in as `reader` or `editor` (staff), password `try-the-widgets`.
`poetry run python manage.py show_page_resolve_order` lists the routes in the order they're tried.
Tests: `poetry run python manage.py test`.

| URL | Shows |
| --- | --- |
| `/articles/` | the first cards rendered with the page, then "load more" from an endpoint that renders the same widget with `arender()` |
| `/articles/latest/` | a redirect from `handle_request()`, and a fixed route tried before `articles/<slug:slug>/` |
| `/articles/<slug>/` | the 404 variant for an unknown slug, the 401 variant for a logged-out reader of a members-only article |
| `/editor/` | staff only: 401 logged out, 403 for a reader |
| `/changelog/` | an ETag built from the articles and the viewer, and a 304 when nothing changed |
| `/about/` | a page routed by hand in `urls.py`, reversed as `about` rather than `website:<name>` |

- `website/pages/site_page.py` is the base page. A page raises `NotLoggedIn`, `NotAllowed` or
  `NotFound` (`website/refusals.py`) from `set_context()`, and `SitePage.handle_request()` renders
  `site_page__unauthorized.html`, `__forbidden.html` or `__not_found.html`, kept beside it.
- The viewer comes from `await request.auser()`, and reaches templates as `page.viewer`. A widget
  template evaluating the lazy `request.user` would run a synchronous query inside the page.
- Widget templates get no context processors, so the logout form takes its token from
  `page.csrf_token`. The login page is Django's `LoginView` with a plain Django template, which
  does get them.
