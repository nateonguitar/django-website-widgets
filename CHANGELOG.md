# Changelog

Each release from 1.0.0, newest first, with what a project changes to upgrade. Versions follow
[semantic versioning](https://semver.org/): a breaking change comes in a new major version.

## 1.0.0

The first stable release. The API is frozen until 2.0, so 1.0 is where the names and shapes
settled. This entry is the upgrade guide from 0.11.

### Upgrading from 0.11

1. Require `django-website-widgets>=1.0,<2`, install it, and run `python manage.py ww_upgrade`.
   That replaces the docs in `website_widgets_docs/` and adds the npm package
   `django-website-widgets` to `package.json`; the steps below are the project's own code.
2. The framework TypeScript moved to that npm package. In the website app's folder:
   - run `npm install`;
   - delete `ts/website_widgets/`, which nothing manages any more;
   - change every import of it to the package name: `import { Controller } from
     "../../ts/website_widgets/controller"` becomes `import { Controller } from
     "django-website-widgets"`, and in `ts/main.ts` the three `export { … } from
     './website_widgets/…'` lines become
     `export { App, Controller, Completer } from 'django-website-widgets';`.
3. Python: move pages onto `AsyncWebPage`, each widget onto `AsyncWidget` (an `async def
   set_context()`) or `SyncWidget` (a plain one, or none), and make the renames under "Python".
4. TypeScript: rename `__element` to `rootElement` in every controller, and replace each
   `getElementByIdOrWarn()` (under "TypeScript").
5. Generator template overrides in `GenerateComponentConfig.templates_dir`: rename them (under
   "Generators"), and drop `__framework_path__` from a controller template, importing from
   `django-website-widgets` instead, since a file under an old name is now ignored.
6. Scripts calling `ww_create_page` or `ww_create_widget`: change `--x=true` to `--x` and
   `--x=false` to `--no-x`.
7. Run the project's tests. The new errors under "Python" name anything left to move.

### Breaking changes

#### Python

- **`Widget` is gone: a widget subclasses `AsyncWidget` or `SyncWidget`.** A widget whose
  `set_context()` is `async def` becomes an `AsyncWidget`; one whose `set_context()` is plain
  `def`, or that has none, a `SyncWidget`, which renders everywhere. Change the import and the
  base class; the wrong kind raises `TypeError` when the class is defined, naming the fix.
  `isinstance(x, Widget)` checks become checks against the two classes.
- **`GenerateComponentConfig(widget_set_context=...)` is removed.** A widget's class is its kind
  now, so `ww_create_widget` writes an `AsyncWidget` by default and a `SyncWidget` with `--sync`.
  Delete the argument from settings.
- **`WebPage` is gone: a page subclasses `AsyncWebPage` or `SyncWebPage`.** Change
  `from website_widgets import WebPage` and `class AppPage(WebPage)` to `AsyncWebPage`, which is
  what `WebPage` was. `SyncWebPage` is new (below).
- **A page's `set_context()`, `handle_request()` and `build_response()` must match its class.**
  On an `AsyncWebPage` each is `async def`; a plain `def` one raises `TypeError` when the class is
  defined, naming the method. A page whose `set_context()` was `def` makes it `async def`; one
  that calls a sync ORM method there moves to the async ORM (`aget`, `async for`) or becomes a
  `SyncWebPage`.
- **`_acall_set_context()` is no longer the way to call a page's `set_context()`.** An overridden
  `handle_request()` calls `await self.set_context()` directly, since the class check guarantees
  it is async.
- **`_debug_label` is `debug_label`.** Rename the attribute where a widget sets it.
- **`reverse_template(viewname, paramnames=...)` is `param_names=`.** Calls passing the list by
  position are unaffected.
- **`NpmWatch` is no longer exported from `website_widgets`.** `start_npm_watch()` is the one
  public name; the class is still in `website_widgets.npm_watch`.
- **`WidgetContext()` takes no `parent` argument.** Nothing passed one; the render pipeline
  shares `context.page` itself.
- **A child widget writing `context.page` before rendering now raises `RuntimeError`.** In 0.x
  those values were silently replaced by the page's shared dict and lost. Write them in the
  child's `set_context()`, where `context.page` is the shared dict, or put the widget's own values
  in `context.data`. A widget rendered on its own, and every page, still write their own
  `context.page` whenever they like.
- **A page placed in `context.children` raises `TypeError`,** naming the key. A page is only ever
  the root, rendered by its view; render a widget there instead.

#### TypeScript

- **The framework TypeScript is the npm package `django-website-widgets`,** no longer copied
  into `ts/website_widgets/`. It is versioned separately from the Python package, which declares
  the npm range it works with: `ww_create_app` writes the range into `package.json`,
  `ww_upgrade` sets it there, and a system check (`website_widgets.W002`) and `ww_doctor` say
  when what is installed is outside it. Controllers import `App`, `Controller` and `Completer`
  from `"django-website-widgets"`. The npm package's changes are in its own changelog,
  `frontend/CHANGELOG.md`.
- **`ww_create_page` and `ww_create_widget` no longer require `ts/website_widgets/`,** and the
  generator placeholder `__framework_path__` is gone; a generated controller imports from the
  npm package.

These change a project's controllers.

- **`Controller.__element` is `rootElement`.** Rename every `this.__element` (and
  `controller.__element`).
- **`getElementByIdOrWarn()` is removed.** Look up inside the root instead,
  `this.rootElement.querySelector('#id')`, so a controller finds only what its own template
  rendered. An element the controller needs that sits outside its root moves inside it, or the
  root's selector moves up to an element containing both.
- **`Controller.dispose()` is removed.** Nothing ever called it. Code in an override wasn't
  running and can be deleted.
- **`Controller.__parentElement` and the root parent's `__childControllers` list are removed.**
  They recorded the root's DOM parent, not the nearest controller. The element's `__controller`
  back-reference stays.

#### Generators

- **Generator templates are named for what they write,** so a project override under an old
  name is ignored until renamed:

  | 0.11 | 1.0 |
  | --- | --- |
  | `page.py.tmpl` | `page__async.py.tmpl`, or `page__sync.py.tmpl` for a `SyncWebPage` base |
  | `page.html.tmpl` | `page__nocontroller.html.tmpl` |
  | `widget.html.tmpl` | `widget__nocontroller.html.tmpl` |
  | `widget__controller.html.tmpl` | `widget__controller__single.html.tmpl` and `widget__controller__repeating.html.tmpl` |
  | `widget__async.py.tmpl`, `widget__sync.py.tmpl` | `widget__async__single.py.tmpl`, `widget__async__repeating.py.tmpl`, `widget__sync__single.py.tmpl`, `widget__sync__repeating.py.tmpl` |

  `page__controller.html.tmpl` keeps its name. Copy the package's template of the new name to
  start a renamed override, so it keeps the placeholders the commands fill.
- **A generated page is routed by its template.** The package's page templates start the class
  with `@register_url('__route__')`. A project's own page template gets a route only once it adds
  `from website_widgets import register_url` and `@register_url('__route__')`; without them it
  keeps working, unrouted, and the command says so.
- **Yes/no options are `--x` / `--no-x` pairs:** `--tscontroller`/`--no-tscontroller`,
  `--stylesheet`/`--no-stylesheet` and `--repeating`/`--no-repeating`, replacing
  `--tscontroller=true|false` and the like. Giving neither still asks.
- **`widget__nocontroller.html.tmpl`'s root has no `id`,** only its class, since nothing selects
  a widget without a controller and a repeated one duplicated the id.

### Added

- **Dialogs a caller awaits,** from the npm package's `DialogController` (npm 1.0.0-rc.2, the
  range this release requires): a dialog's widget renders a `<template>` of its content, and
  `const answer = await MyDialogController.show(...)` opens a `<dialog>` around a copy of it.
  `dialogs.md` has the pattern.
- **`ww_create_dialog <name>`** writes a dialog into `widgets/`: a `SyncWidget` rendering its
  `<template>`, and a `DialogController<void>` whose static `show()` opens it, exported from
  `main.ts`, with the stylesheet asked about or `--stylesheet`. Its templates are
  `dialog.py.tmpl`, `dialog.html.tmpl` and `dialog_controller.ts.tmpl`, overridable in
  `templates_dir` like the others.
- **`SyncWebPage`,** for a page with no async work: its `set_context()` is `def`, it runs with no
  event loop, so the ORM works as in any Django view, and every widget in it is a `SyncWidget`.
  `AsyncWebPage` remains the one to use.
- **`ww_create_page` routes the page it creates,** at a route made from its name
  (`account/settings_page` to `account/settings`) or `--route`, stopping on a route name already
  taken or an unknown converter and warning when the route ties with another page's.
- **Both generators end with a summary** of each file written: the class, the root's selector,
  what `main.ts` took, and for a page its URL and the name it reverses by.
- **`ww_create_widget` writes a widget for single use or for repeating,** asking when it has a
  controller, or `--repeating`. A repeating widget takes a keyword-only `key`, carried on its
  root as `data-key` and in its controller's selector.
- **A nested name's new folders get an `__init__.py`,** so `ww_create_widget
  emails/email_document` makes `widgets/emails/` a package rather than a namespace package.
- **Clearer errors:** reading `self.request` in a constructor says it isn't set until rendering
  starts and to read it in `set_context()`; a `SyncWebPage` given an async widget says how to fix
  it.
- **The controller shape the generators write and the docs teach:** a controller's `Elements`
  class finds its own fields in `findIn(root)`, typed by the field alone
  (`this.saveButton = root.querySelector('.editor__save')`), replacing a `buildElements()` on the
  controller. Existing controllers keep working; this is guidance, not a requirement.
- **Generated widgets and pages carry one comment on `set_context()`,** saying it runs when
  rendering starts and is where queries, `self.request` and `self.context.page` belong.
- **A `py.typed` marker,** so type checkers read the package's type hints.
- **A `Changelog` link on PyPI,** to this file.

## Before 1.0.0

The 0.x releases, 0.1.0 to 0.11.0, broke the API freely and have no entries here. Their tags
(`v0.1.0` to `v0.11.0`) and the git history between them record what changed.
