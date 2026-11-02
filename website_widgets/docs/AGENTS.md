# django-website-widgets

The index of this package's documentation, for AI coding assistants and anyone changing a site
built on it. One line per doc, each beside this file, enough to pick the right one; the detail is
in the doc.

## Rules every change follows

- **A page is an `AsyncWebPage` subclass (a `SyncWebPage` only for a page with no async work), a
  component an `AsyncWidget` or `SyncWidget` subclass,** each in its own folder with
  its template beside its `.py` file and named after it (`info_card.py` renders
  `info_card.html`). Create one with `python manage.py ww_create_page`, `ww_create_widget` or, for a dialog,
  `ww_create_dialog`, not by hand. A variant render is `<name>__<variant>.html`, chosen by setting
  `template_filename` to a bare file name.
- **Data flows down, through constructors.** A widget's `set_context()` builds its children, and
  a parent never reads a child's context. What every widget needs goes in `context.page`.
- **A template sees four keys:** `request`, `page`, `data`, `children`, with no context
  processors and no `user`; a page puts the user in `context.page` itself, loaded with
  `await self.request.auser()` under Django's auth middleware (`rendering_pipeline.md`).
- **A page reaches a URL by `@register_url` on its class,** in a module under the website app's
  `pages/` folder, or by hand in `urls.py` with its class's `as_view()`.
- **Outside a page, a widget renders with `render()`** from sync code or `await arender()` from
  async code, never by calling its template. A whole document that answers no request, such as
  an HTML email, is a widget whose template is the document, never a page, which answers a web
  request.
- **A widget's frontend is a `Controller` subclass,** started by
  `App.initController(new MyController(), '#root')` from the widget's `<script>`. The framework
  TypeScript (`App`, `Controller`, `Completer`, `DialogController`) is the npm package `django-website-widgets`,
  imported by that name; **never edit it in `node_modules/`**, subclass `Controller` or `App`
  instead, and keep project state in the project's own classes.

## Docs

- `rendering_pipeline.md` — what runs between a request and HTML: async vs sync pages, one page instance per request, the passes of `build_response()`, constructor vs `set_context()`, the user and the async ORM trap
- `rendering_a_widget_alone.md` — `render()` and `arender()` outside a page: sync vs async, no request, a whole document (email) as a widget, inserting a fragment so its scripts run
- `templates.md` — what a template sees (the four keys, the silent missing-`data.` trap), how its file is found, variant templates, no `{% include %}`
- `routing.md` — `@register_url` or by hand: discovery under `pages/`, names and the namespace, most-specific-first order, the tie check, `ww_show_routes`
- `frontend_controllers.md` — the framework TypeScript: a controller's lifecycle, selector and shape (`Elements`, `findIn()`, `setState()`), singletons and `Completer`, what it leaves to the project
- `dialogs.md` — a dialog its caller awaits: the widget's `<template>`, `DialogController`'s `show()` and `answer()`, the `data-dialog-*` attributes, dismissal
- `reverse_template.md` — `reverse_template()`: URL names into `/posts/{post_id}` templates for the frontend
- `creating_pages_and_widgets.md` — `ww_create_page`, `ww_create_widget` and `ww_create_dialog`: what they write and their options, routing a new page, repeating widgets, `main.ts`, overriding their templates
- `creating_and_upgrading_an_app.md` — `ww_create_app` and `ww_upgrade`: the app's name, what each writes, the build files, the npm range, the managed docs folder, the docs pointer
- `starter_site.md` — the site `ww_create_app` writes: each file's job, `AppPage` and refusals, `AppState` vs `data-` attributes, `AppUrls`, the endpoint
- `checking_the_setup.md` — the system checks (E001–E003, W001, W002) and their fixes, `ww_doctor`
- `npm_watch.md` — `start_npm_watch()` in `manage.py`: when it starts `npm run watch` and how it avoids a second watcher
- `node_and_package_managers.md` — installing Node, building in a container instead, `node_modules` across OSes, yarn, pnpm and the rest

## Lessons

Techniques shown with worked code, for the cases the docs above explain but don't walk through.

- `loading_data.md` — querying in `async def set_context()`, `select_related`, when gathering slow calls in a parent helps
- `widgets_in_plain_django.md` — widgets in an ordinary view, a plain template, the admin, a form field
- `html_emails.md` — an email as an `EmailDocument` widget: no request, absolute links, the plain-text version
- `etags_and_304s.md` — answering 304 from `handle_request()` before the tree is built, the ETag, `Vary: Cookie`
- `deploying_the_frontend.md` — the production build, building in the deploy, cache busting with `ManifestStaticFilesStorage`
