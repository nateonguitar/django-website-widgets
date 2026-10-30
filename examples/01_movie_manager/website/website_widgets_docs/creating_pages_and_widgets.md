# Creating a page or widget

`python manage.py ww_create_page <name>` and `python manage.py ww_create_widget <name>` write a new
component's files into the website app and register its controller and stylesheet in
`ts/main.ts`. Read this before adding a component by hand, or before changing what the commands
write for a project.

Primary code:
- `website_widgets.management.commands.ww_create_page` and `website_widgets.management.commands.ww_create_widget` — the commands
- `website_widgets.management.component_files.ComponentFiles` — the file work both call: a file from a template, a line in `main.ts`
- `website_widgets.config.GenerateComponentConfig` — their three settings
- the package's `generator_templates/` — the default templates, listed below

## What it writes

```
python manage.py ww_create_widget like_button --tscontroller=true --stylesheet=true
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
`--tscontroller` or `--stylesheet`, the command asks. It stops without writing anything when the
name breaks that rule or the folder already exists.

**The root element's id and class are the module name in kebab case** (`like-button`), and a
page's root is a `<main>` holding an `<h1>`. The generated controller takes the root's selector,
`await LikeButtonController.initializeController('#like-button')`, and looks its elements up
inside that root, so a widget shown several times on a page works once each root has its own id
(`like-button-{{ data.movie.id }}`, passed the same way). The one example value, `label`, shows
how data reaches a controller: `set_context()` puts it in `context.data`, the template writes it
in a `data-` attribute on the root, and the controller reads it from `this.__element.dataset` and
writes it in `setState()`.

**A widget's `set_context()` is `async def` unless the project or the command says otherwise.**
Async is right for a widget in a page or behind `arender()`, where a database query is awaited; a
sync `def set_context()` runs on the page's event loop, where a sync query raises
`SynchronousOnlyOperation`. Sync is right for a widget rendered with `render()` from sync code (a
plain Django view, an email, the admin), which refuses an `async def`. `--async` or `--sync`
chooses for one widget; `GenerateComponentConfig.widget_set_context` (`'async'` or `'sync'`) sets
the project's default. A page is always async, since a page only renders through the async
pipeline, and calls no `super().set_context()`, since `WebPage`'s does nothing; a project whose
page base class does work there adds the call in its own `page.py.tmpl`.

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
  (`starter_site.md`). When nothing is at that path, or it isn't a `WebPage`,
  the command stops before writing anything, rather than writing a page that fails on import.

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
| `page.py.tmpl` | a page's class |
| `widget__async.py.tmpl`, `widget__sync.py.tmpl` | a widget's class, with `async def` or `def set_context()` |
| `page.html.tmpl`, `widget.html.tmpl` | the template, with no controller |
| `page__controller.html.tmpl`, `widget__controller.html.tmpl` | the template, starting the controller |
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
| `__app_page_module__`, `__AppPageClass__` | the two halves of `app_page_class`, in `page.py.tmpl` |

Copy the package's template to start an override, so it keeps the placeholders the command fills.
