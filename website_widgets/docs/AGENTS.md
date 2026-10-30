# django-website-widgets

The index of this package's documentation, for AI coding assistants and anyone changing a site
built on it. One line per doc, each beside this file, enough to pick the right one; the detail is
in the doc.

## Rules every change follows

- **A page is a `WebPage` subclass, a component a `Widget` subclass,** each in its own folder with
  its template beside its `.py` file and named after it (`info_card.py` renders
  `info_card.html`). Create one with `python manage.py ww_create_page` or `ww_create_widget`, not by hand. A variant render is `<name>__<variant>.html`, chosen by setting
  `template_filename` to a bare file name.
- **Data flows down, through constructors.** A widget's `set_context()` builds its children, and
  a parent never reads a child's context. What every widget needs goes in `context.page`.
- **A template sees four keys:** `request`, `page`, `data`, `children`. No context processors
  run, and there's no `user`: a page puts the user in `context.page` itself, since whether
  reading `request.user` in a page is safe depends on the project's middleware. With Django's
  `AuthenticationMiddleware` it's lazy and raises `SynchronousOnlyOperation`, so load it with
  `await self.request.auser()` (`rendering_pipeline.md`).
- **A page reaches a URL by `@register_url` on its class,** in a module under the website app's
  `pages/` folder, or by hand in `urls.py` with `WebPage.as_view()`.
- **Outside a page, a widget renders with `render()`** from sync code or `await arender()` from
  async code, never by calling its template. A whole document that answers no request, such as
  an HTML email, is a widget whose template is the document, never a `WebPage`, which answers a
  web request.
- **A widget's frontend is a `Controller` subclass,** started by `App.initializeController()`
  from the widget's `<script>`. **Never edit the framework's TypeScript files** (`app.ts`,
  `controller.ts`, `completer.ts`); subclass `Controller` or `App` instead, and keep project
  state in the project's own classes.

## Docs

- `rendering_pipeline.md` — what happens between a request and HTML: one page instance per request, the four passes of `build_response()`, `render()` and `arender()` outside a page, a whole document with no request (email) as a widget, the four-key template context and why it has no `user`, template lookup, and the async ORM trap
- `routing.md` — routing a page by hand or with `@register_url`: discovery under `pages/`, the namespace and default names, most-specific-first ordering, the tie check, `ww_show_routes`
- `frontend_controllers.md` — the framework TypeScript: why it is never edited, a controller's lifecycle, `setState()`, element lookups, singletons and `Completer`, what `Controller` leaves to the project
- `reverse_template.md` — `reverse_template()`: URL names into `/posts/{post_id}` templates for the frontend, why it reads the route, `paramnames`, why it isn't called `reverse`
- `creating_pages_and_widgets.md` — `ww_create_page` and `ww_create_widget`: the files they write, registering in `main.ts`, what they need first, `app_page_class`, overriding their templates with `templates_dir`, the placeholders
- `creating_and_upgrading_an_app.md` — `ww_create_app` and `ww_upgrade`: why the app's name comes only from settings, what each writes, the next steps, the build files an upgrade asks about or checks, the two managed folders file by file (these docs in `website_widgets_docs/`, the TypeScript in `ts/website_widgets/`), the version and file list in each README, what an upgrade deletes, the out-of-date warning, the docs pointer
- `starter_site.md` — the site `ww_create_app` writes: each file's job, `AppPage` and its refusal exceptions, `AppState` vs `data-` attributes, `AppUrls` and why static URLs go through it, the REST-agnostic endpoint, the build files as the developer's to change
- `checking_the_setup.md` — the package's system checks (E001–E003, W001) and their fixes, `ww_doctor`'s checklist, the `package.json` check
- `npm_watch.md` — `start_npm_watch()` in `manage.py`: when it starts `npm run watch`, how it avoids a second watcher, why it sets Django up early
