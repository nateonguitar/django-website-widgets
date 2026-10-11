# django-website-widgets

The index of this package's documentation, for AI coding assistants and anyone changing a site
built on it. One line per doc, enough to pick the right one; the detail is in the doc.

## Rules every change follows

- **A page is a `Page` subclass, a component a `Widget` subclass,** each in its own folder with
  its template beside its `.py` file and named after it (`info_card.py` renders
  `info_card.html`). Create one with `python manage.py generate_component`, not by hand. A variant render is `<name>__<variant>.html`, chosen by setting
  `template_filename` to a bare file name.
- **Data flows down, through constructors.** A widget's `set_context()` builds its children, and
  a parent never reads a child's context. What every widget needs goes in `context.page`.
- **A template sees five keys:** `request`, `user`, `page`, `data`, `children`. No context
  processors run.
- **A page reaches a URL by `@register_url` on its class,** in a module under the website app's
  `pages/` folder, or by hand in `urls.py` with `Page.as_view()`.
- **Outside a page, a widget renders with `render()`** from sync code or `await arender()` from
  async code, never by calling its template.
- **A widget's frontend is a `Controller` subclass,** started by `App.initializeController()`
  from the widget's `<script>`. **Never edit the framework's TypeScript files** (`app.ts`,
  `controller.ts`, `completer.ts`); subclass `Controller` or `App` instead, and keep project
  state in the project's own classes.

## Docs

- `docs/rendering_pipeline.md` — what happens between a request and HTML: one page instance per request, the four passes of `build_response()`, `render()` and `arender()` outside a page, the five-key template context, template lookup, and the async ORM trap
- `docs/routing.md` — routing a page by hand or with `@register_url`: discovery under `pages/`, the namespace and default names, most-specific-first ordering, the tie check, `show_page_resolve_order`
- `docs/frontend_controllers.md` — the framework TypeScript: why it is never edited, a controller's lifecycle, `setState()`, element lookups, singletons and `Completer`, what `Controller` leaves to the project
- `docs/reverse_template.md` — `reverse_template()`: URL names into `/posts/{post_id}` templates for the frontend, why it reads the route, `paramnames`, why it isn't called `reverse`
- `docs/generate_component.md` — `generate_component`: the files it writes, registering in `main.ts`, what it needs first, `app_page_class`, overriding its templates with `templates_dir`, the placeholders
- `docs/init_website_widgets.md` — `init_website_widgets`: what it copies into `ts/website_widgets/`, why file by file, the version and file list in the README, what a rerun deletes, the docs pointer
- `docs/npm_watch.md` — `start_npm_watch()` in `manage.py`: when it starts `npm run watch`, how it avoids a second watcher, why it sets Django up early
