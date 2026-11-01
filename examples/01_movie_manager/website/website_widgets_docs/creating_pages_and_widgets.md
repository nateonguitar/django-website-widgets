# Creating a page or widget

`python manage.py ww_create_page <name>` and `python manage.py ww_create_widget <name>` write a new
component's files into the website app and register its controller and stylesheet in
`ts/main.ts`; `ww_create_page` also routes the page. Read this before adding a component by hand,
or before changing what the commands write for a project.

Primary code:
- `website_widgets.management.commands.ww_create_page` and `website_widgets.management.commands.ww_create_widget` — the commands
- `website_widgets.management.component_files.ComponentFiles` — the file work both call: a file from a template, a line in `main.ts`
- `website_widgets.config.GenerateComponentConfig` — their three settings
- the package's `generator_templates/` — the default templates, listed below

## What it writes

```
python manage.py ww_create_widget like_button --tscontroller --stylesheet
```

writes `<website app>/widgets/like_button/` (`ww_create_page` writes into `pages/`):

```
__init__.py         from .like_button import LikeButton
like_button.py      class LikeButton(Widget), with an async set_context()
like_button.html    its template: a root <div id="like-button">, starting the controller when there is one
like_button.ts      class LikeButtonController extends Controller   (--tscontroller)
like_button.scss    empty                                            (--stylesheet)
```

The class name is the module name in PascalCase. A name with folders, such as
`dialogs/login_dialog`, nests the component, and every relative import is worked out from where
it lands. Each part of the name becomes a Python package or module, which route discovery
imports, so each must be a lowercase identifier (`login_dialog`, not `LoginDialog`,
`login-dialog` or `class`), and `..` can't climb out of `pages/` or `widgets/`. Without
`--tscontroller`, `--stylesheet` or, for a widget with a controller, `--repeating`, the command
asks. It stops without writing anything when the
name breaks that rule or the folder already exists. It ends by listing the files it wrote, each
with what it holds: the class, the root's selector, whether `main.ts` took the controller and the
stylesheet, and for a page its URL and the name it reverses by.

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
since nothing looks its root up, and so repeats as it is. The generated `<script>` starts the controller on
that root, `await App.initController(new LikeButtonController(), '#like-button')`, and the
controller's `Elements` finds its elements inside that root, in `findIn()`. The one example value, `label`, shows how data
reaches a controller: `set_context()` puts it in `context.data`, the template writes it in a
`data-` attribute on the root, and the controller reads it from `this.rootElement.dataset` and
writes it in `setState()`.

**A widget with a controller is written for single use or for repeating**, which the command asks
(`Shown more than once on a page? [y/N]`) and `--repeating` or `--no-repeating` answers. Every
yes/no option is such a pair, `--tscontroller`/`--no-tscontroller` and
`--stylesheet`/`--no-stylesheet` too, and giving neither asks. A repeating widget,
such as one card per search result, has no id: every instance shares the class, and each root
carries its own key in `data-key`, which the selector finds it by, so each gets its own
controller. Its class takes the key as a keyword-only argument, `MovieCard(key=movie.id)`, and its
constructor puts it straight into `context.data['key']`, which `super().__init__()` has just
created, so `set_context()` has nothing to copy. Its template writes:

```html
<div class="movie-card"
     data-key="{{ data.key }}">
...
await App.initController(new MovieCardController(), '.movie-card[data-key="{{ data.key }}"]');
```

The controller can read the key from `dataset.key`; a value the controller needs under its own
name, such as the movie manager card's `data-movie-id`, sits beside it even when it holds the same
id. The key goes inside a quoted attribute selector, so anything without a double quote works; a primary key
or a slug is usual. A widget without a controller isn't asked: nothing selects its root, which
has only its class, so the same template serves one instance or many, and `--repeating` changes
nothing.

**A widget's `set_context()` is `async def` unless the project or the command says otherwise.**
Async is right for a widget in a page or behind `arender()`, where a database query is awaited; a
sync `def set_context()` runs on the page's event loop, where a sync query raises
`SynchronousOnlyOperation`. Sync is right for a widget rendered with `render()` from sync code (a
plain Django view, an email, the admin), which refuses an `async def`. `--async` or `--sync`
chooses for one widget; `GenerateComponentConfig.widget_set_context` (`'async'` or `'sync'`) sets
the project's default. A page has no flag: its `set_context()` must match its class, so the
command reads it from the page base class, writing `page__async.py.tmpl`'s `async def` under an
`AsyncWebPage` and `page__sync.py.tmpl`'s `def` under a `SyncWebPage`. It calls no
`super().set_context()`, since the base's does nothing; a project whose page base class does work
there adds the call in its own page template.

**`ts/main.ts` gets the new lines between its marker pairs**, each section kept sorted:
`// {{ WIDGET STYLES START }}` / `END`, `PAGE STYLES`, `WIDGET CONTROLLERS` and
`PAGE CONTROLLERS`. A stylesheet becomes `import '../widgets/like_button/like_button.scss';` and
a controller `export { LikeButtonController } from '../widgets/like_button/like_button';`,
which is what lets a template `import { LikeButtonController } from '{% static "main.js" %}'`.
When `main.ts` or a marker pair is missing, the files are still written and the command says
which line to add by hand.

## What it needs first

- **The framework files.** A generated controller imports `App` and `Controller` from
  `ts/website_widgets/`, so the command stops, pointing at `ww_upgrade`, when
  `app.ts` or `controller.ts` isn't there.
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
| `widget__async__single.py.tmpl`, `widget__sync__single.py.tmpl` | a widget's class, with `async def` or `def set_context()` |
| `widget__async__repeating.py.tmpl`, `widget__sync__repeating.py.tmpl` | a repeating widget's class, taking `key=` |
| `page__nocontroller.html.tmpl`, `widget__nocontroller.html.tmpl` | the template, with no controller |
| `page__controller.html.tmpl`, `widget__controller__single.html.tmpl` | the template, starting the controller |
| `widget__controller__repeating.html.tmpl` | a repeating widget's template, its key in the root's `data-key` |
| `controller.ts.tmpl` | the controller, for pages and widgets |
| `component.scss.tmpl` | the stylesheet, for pages and widgets |

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
| `__framework_path__` | the relative import path to `ts/website_widgets`, such as `../../ts/website_widgets` |
| `__app_page_module__`, `__AppPageClass__` | the two halves of `app_page_class`, in the page templates |
| `__route__` | the page's route, in the page templates' `@register_url('__route__')` |

Copy the package's template to start an override, so it keeps the placeholders the command fills.
