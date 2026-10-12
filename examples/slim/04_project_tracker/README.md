# Project tracker

A small working app using everything the other examples show: pages with an appbar and footer,
access-denied and not-found variants, Django's own logins, and creating, editing and deleting
projects through JSON endpoints, all on real models.

```bash
poetry install
poetry run python manage.py migrate
poetry run python manage.py runserver
```

Then open http://localhost:8000/ and log in as `user_1`, `user_2` or `admin` (staff), password
`try-the-widgets`. Tests: `poetry run python manage.py test`.

- `website/pages/tracker_page.py` is the base page: the viewer from `await request.auser()`, the
  appbar and footer as children the document template renders, flash messages, and the 401, 403
  and 404 variants (`tracker_page__*.html`) it renders when a page raises.
- `website/api/` holds the endpoints, one class per HTTP method, routed in `example_site/urls.py`.
  Logging in uses Django's async auth (`aauthenticate`, `alogin`, `alogout`).
- Who can see a project is checked where it's used, in each page and endpoint: staff see every
  project, everyone else only their own.
- Every query a template reads `created_by` from uses `select_related('created_by')`: following
  the foreign key lazily in a template would run a synchronous query inside the async page.
- `website/static/website/api.js` is the fetch helper every page's script uses, loaded once by the
  document template beside `analytics.js`. It reads the CSRF token and the flash cookie's name
  from `<meta>` tags, since a static file can't use template values. Each page's own behaviour
  (the login form, editing a project) stays an inline `<script>` in its template.
