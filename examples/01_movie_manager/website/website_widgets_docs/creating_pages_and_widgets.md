# Creating a page, widget or dialog

`python manage.py ww_create_page <name>`, `python manage.py ww_create_widget <name>` and
`python manage.py ww_create_dialog <name>` write a new component's files into the website app and
register its controller and stylesheet in `ts/main.ts`; `ww_create_page` also routes the page.
Read this before adding a component by hand, or before changing what the commands write for a
project.

Primary code:
- `website_widgets.management.commands.ww_create_page`, `website_widgets.management.commands.ww_create_widget` and `website_widgets.management.commands.ww_create_dialog` — the commands
- `website_widgets.management.component_files.ComponentFiles` — the file work they all call: a file from a template, a line in `main.ts`
- `website_widgets.config.GenerateComponentConfig` — their two settings
- the package's `generator_templates/` — the default templates, listed below

## What it writes

```
python manage.py ww_create_widget like_button --tscontroller --stylesheet
```

writes `<website app>/widgets/like_button/` (`ww_create_page` writes into `pages/`):

```
__init__.py         from .like_button import LikeButton
like_button.py      class LikeButton(AsyncWidget), with an async set_context()
like_button.html    its template: a root <div id="like-button">, starting the controller when there is one
like_button.ts      class LikeButtonController extends Controller   (--tscontroller)
like_button.scss    empty                                            (--stylesheet)
```

The class name is the module name in PascalCase. A name with folders, such as
`dialogs/login_dialog`, nests the component, and every relative import is worked out from where
it lands. A folder the name adds, `dialogs/` here, gets an empty `__init__.py`, so it imports as a
package like every other, and the summary says so; a folder that already exists is left as it is.
Each part of the name becomes a Python package or module, which route discovery
imports, so each must be a lowercase identifier (`login_dialog`, not `LoginDialog`,
`login-dialog` or `class`), and `..` can't climb out of `pages/` or `widgets/`. Each yes/no
option is a pair (`--tscontroller`/`--no-tscontroller`, `--stylesheet`/`--no-stylesheet`,
`--repeating`/`--no-repeating`), and giving neither asks. It stops without writing anything when
the name breaks that rule or the folder already exists. It ends by listing the files it wrote, each
with what it holds: the class, the root's selector, whether `main.ts` took the controller and the
stylesheet, and for a page its URL and the name it reverses by.

**The commands only write into the website app,** with no flag for another destination: that
app's `tsconfig.json`, `package.json` and webpack config are the frontend build that bundles what
they write. A widget belonging to another app is made by hand, as the movie manager's admin-only
`ReturnRentalField` is, in `api/admin/widgets/return_rental_field/`.

**A page is routed by its template.** The package's page templates start the class with
`@register_url('__route__')`, named after the class (`routing.md`), and the command fills in a
route made from the name: the path in kebab case with a trailing `_page` dropped, so `login_page`
routes to `login`, `manage_auth_tokens_page` to `manage-auth-tokens` and `account/settings_page`
to `account/settings`. `--route=<route>` gives another, and `--route=` is the site root. A
project that routes its pages some other way leaves the decorator out of its own page templates
(below), and its pages are written without one; the command then says the page isn't routed and
prints the `@register_url` to add, or the import and `path()` for `urls.py`.

When the template has `__route__`, the command stops before writing anything on a route naming a
converter Django doesn't have, and on a page whose class name another page's route already uses
as its name, since two routes with one name fail every import of the pages. A route that ties
with another page's, matching the same URLs with neither more specific, is written with a
warning, since the `website_widgets.E001` check then fails until one of them changes.

**The root element's id and class are the module name in kebab case** (`like-button`), and a
page's root is a `<main>` holding an `<h1>`. A widget without a controller has only the class,
since nothing looks its root up, and so repeats as it is. The one example value, `label`, shows
how data reaches a controller: `set_context()` puts it in `context.data`, the template writes it
in a `data-` attribute on the root, and the controller reads it from `this.rootElement.dataset`
and writes it in `setState()`.

**A widget with a controller is written for single use or for repeating**: the command asks
(`Shown more than once on a page? [y/N]`), `--repeating` or `--no-repeating` answers. A repeating
widget, such as one card per search result, has no id. Its class takes a keyword-only `key`
(`MovieCard(key=movie.id)`), which the constructor puts straight into `context.data['key']`, and
its template carries it in `data-key` and selects on it:

```html
<div class="movie-card"
     data-key="{{ data.key }}">
...
await App.initController(new MovieCardController(), '.movie-card[data-key="{{ data.key }}"]');
```

The key sits inside a quoted attribute selector, so anything without a double quote works; a
primary key or a slug is usual. A value the controller needs under its own name, such as the
movie manager card's `data-movie-id`, sits beside it even when it holds the same id. A widget
without a controller isn't asked, since nothing selects its root.

**A widget is an `AsyncWidget` unless the command is told `--sync`.** `AsyncWidget` is for a
widget in an `AsyncWebPage` or behind `arender()`; `SyncWidget` for one rendered with `render()`
from sync code (a plain Django view, an email, the admin) or in a `SyncWebPage`
(`rendering_pipeline.md`). A page has no flag: the command reads the kind from the page base
class and writes `page__async.py.tmpl` or `page__sync.py.tmpl`. Neither calls
`super().set_context()`, since the base's does nothing; a project whose page base class does work
there adds the call in its own page template.

**The generated constructor only stores its arguments; `set_context()`, marked by the generated
comment, does the rest** (`rendering_pipeline.md` says why, and what fails loudly otherwise).

**`ts/main.ts` gets the new lines between its marker pairs**, each section kept sorted:
`// {{ WIDGET STYLES START }}` / `END`, `PAGE STYLES`, `WIDGET CONTROLLERS` and
`PAGE CONTROLLERS`. A stylesheet becomes `import '../widgets/like_button/like_button.scss';` and
a controller `export { LikeButtonController } from '../widgets/like_button/like_button';`,
which is what lets a template `import { LikeButtonController } from '{% static "main.js" %}'`.
When `main.ts` or a marker pair is missing, the files are still written and the command says
which line to add by hand.

## Creating a dialog

```
python manage.py ww_create_dialog confirm_dialog --stylesheet
```

writes `<website app>/widgets/confirm_dialog/`, since a dialog is a widget:

```
__init__.py           from .confirm_dialog import ConfirmDialog
confirm_dialog.py     class ConfirmDialog(SyncWidget), putting the title in context.data
confirm_dialog.html   <template id="confirm-dialog-template" data-dialog-class="confirm-dialog">
confirm_dialog.ts     class ConfirmDialogController extends DialogController<void>, with show()
confirm_dialog.scss   empty                                                     (--stylesheet)
```

The pieces are those `dialogs.md` describes: the template holds a
title marked `data-dialog-label` and a Close button marked `data-dialog-close`, and the
controller's static `show()` calls `DialogController.openDialog()` with the template's id. The
name is used as given, as `ww_create_widget` uses it, with no `_dialog` added or dropped, and a
nested name, a bad name or an existing folder are treated the same way.

**A dialog has fewer options than a widget,** because its shape leaves nothing to choose:

- **No `--async`/`--sync`.** Its widget renders a `<template>` and loads nothing, so it is
  always a `SyncWidget`, and renders in an async or a sync page alike.
- **No `--tscontroller`.** `show()` is the only way to open a dialog, so the controller is
  always written and exported from `main.ts`.
- **No `--repeating`.** The widget is placed once wherever the dialog can open, and each
  `show()` copies the template into a `<dialog>` of its own, so nothing inside it has an id
  and no key is needed.

Only the stylesheet is asked about, `--stylesheet` or `--no-stylesheet` answering. The `<dialog>`
the package creates is bare, so a dialog usually wants one, at least for its width and padding,
under the class in `data-dialog-class`.

**The generated dialog answers nothing** (`DialogController<void>`). A dialog that answers a
value changes `void` to its type, keeps the answer in a typed field set before
`this.dialog.close()`, and returns the field from `answer()` (`dialogs.md`).

**Using it takes two steps,** which the command prints when it finishes: place the widget as a
child of the page or widget the dialog opens from (or of the document template, when every page
can open it), and open it with `await ConfirmDialogController.show()`.

## What it needs first

- **The npm package, to build.** A generated controller imports `Controller` from
  `django-website-widgets`, the npm package `package.json` depends on. The command writes the
  file either way; the build needs the package installed (`ww_doctor` checks it).
- **A page base class, for a page.** A generated page subclasses the class at
  `GenerateComponentConfig.app_page_class`, which defaults to
  `<website_app_name>.pages.app_page.AppPage`, where `ww_create_app`'s starter site puts it
  (`starter_site.md`). When nothing is at that path, or it is neither an `AsyncWebPage` nor a
  `SyncWebPage`, the command stops before writing anything, rather than writing a page that fails on import.

## A project's own templates

The package's templates hold no project opinions: no logging, no CSP nonce, no HTTP client, and
no layout beyond a root element. A project bakes its conventions in by keeping its own templates
in `GenerateComponentConfig.templates_dir`. **A file there replaces the package's template of the
same name**, and the others keep the package's, the way a project overrides one Django admin
template. Pages and widgets have separate templates, so a site can wrap every page in its layout
without wrapping every widget in it:

| Template | Writes |
| --- | --- |
| `__init__.py.tmpl` | `__init__.py` |
| `page__async.py.tmpl`, `page__sync.py.tmpl` | a page's class, with its `@register_url` and `async def` or `def set_context()`, for an `AsyncWebPage` or `SyncWebPage` base |
| `widget__async__single.py.tmpl`, `widget__sync__single.py.tmpl` | a widget's class, an `AsyncWidget` or a `SyncWidget` |
| `widget__async__repeating.py.tmpl`, `widget__sync__repeating.py.tmpl` | a repeating widget's class, taking `key=` |
| `page__nocontroller.html.tmpl`, `widget__nocontroller.html.tmpl` | the template, with no controller |
| `page__controller.html.tmpl`, `widget__controller__single.html.tmpl` | the template, starting the controller |
| `widget__controller__repeating.html.tmpl` | a repeating widget's template, its key in the root's `data-key` |
| `controller.ts.tmpl` | the controller, for pages and widgets |
| `dialog.py.tmpl` | a dialog's class, a `SyncWidget` |
| `dialog.html.tmpl` | a dialog's `<template>` |
| `dialog_controller.ts.tmpl` | a dialog's controller, a `DialogController` with `show()` |
| `component.scss.tmpl` | the stylesheet, for pages, widgets and dialogs |

```python
from website_widgets.config import GenerateComponentConfig, WebsiteWidgetsConfig

WEBSITE_WIDGETS = WebsiteWidgetsConfig(
    generate_component=GenerateComponentConfig(
        templates_dir=BASE_DIR / 'website' / 'generator_templates',
    ),
)
```

A template's placeholders are replaced as plain text, since `{{ }}` and `{% %}` already mean
something in an HTML template and `${...}` in TypeScript:

| Placeholder | Becomes |
| --- | --- |
| `__ClassName__` | `LikeButton` |
| `__module_name__` | `like_button` |
| `__css_name__` | `like-button`, the root element's id and class |
| `__app_page_module__`, `__AppPageClass__` | the two halves of `app_page_class`, in the page templates |
| `__route__` | the page's route, in the page templates' `@register_url('__route__')` |

Copy the package's template to start an override, so it keeps the placeholders the command fills.
