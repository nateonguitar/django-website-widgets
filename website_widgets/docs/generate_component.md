# Generating a page or widget

`python manage.py generate_component <page|widget> <name>` writes a new component's files into the
website app and registers its controller and stylesheet in `ts/main.ts`. Read this before adding
a component by hand, or before changing what the generator writes for a project.

Primary code:
- `website_widgets.management.commands.generate_component` — the command
- `website_widgets.config.GenerateComponentConfig` — its two settings
- the package's `generator_templates/` — the default templates, listed below

## What it writes

```
python manage.py generate_component widget like_button --tscontroller=true --stylesheet=true
```

writes `<website app>/widgets/like_button/` (a page goes in `pages/`):

```
__init__.py         from .like_button import LikeButton
like_button.py      class LikeButton(Widget)
like_button.html    its template, starting the controller when there is one
like_button.ts      class LikeButtonController extends Controller   (--tscontroller)
like_button.scss    empty                                            (--stylesheet)
```

The class name is the module name in PascalCase. A name with folders, such as
`dialogs/login_dialog`, nests the component, and every relative import is worked out from where
it lands. Without `--tscontroller` or `--stylesheet`, the command asks. It stops without writing
anything when the folder already exists.

**`ts/main.ts` gets the new lines between its marker pairs**, each section kept sorted:
`// {{ WIDGET STYLES START }}` / `END`, `PAGE STYLES`, `WIDGET CONTROLLERS` and
`PAGE CONTROLLERS`. A stylesheet becomes `import '../widgets/like_button/like_button.scss';` and
a controller `export { LikeButtonController } from '../widgets/like_button/like_button';`,
which is what lets a template `import { LikeButtonController } from '{% static "main.js" %}'`.
When `main.ts` or a marker pair is missing, the files are still written and the command says
which line to add by hand.

## What it needs first

- **The framework files.** A generated controller imports `App` and `Controller` from
  `ts/website_widgets/`, so the command stops, pointing at `init_website_widgets`, when
  `app.ts` or `controller.ts` isn't there.
- **A page base class, for a page.** A generated page subclasses the class at
  `GenerateComponentConfig.app_page_class`, which defaults to
  `<website_app_name>.pages.app_page.AppPage`. When nothing is at that path, or it isn't a `WebPage`,
  the command stops before writing anything, rather than writing a page that fails on import.

## A project's own templates

The package's templates hold no project opinions: no logging, no CSP nonce, no HTTP client, and
a page that is a plain sync `set_context()`. A project bakes its conventions in by keeping its
own templates in `GenerateComponentConfig.templates_dir`. **A file there replaces the package's
template of the same name**, and the others keep the package's, the way a project overrides one
Django admin template:

| Template | Writes |
| --- | --- |
| `__init__.py.tmpl` | `__init__.py` |
| `page.py.tmpl` | a page's class |
| `widget.py.tmpl` | a widget's class |
| `component.html.tmpl` | the template, with no controller |
| `component__controller.html.tmpl` | the template, starting the controller |
| `controller.ts.tmpl` | the controller |
| `component.scss.tmpl` | the stylesheet |

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
| `__framework_path__` | the relative import path to `ts/website_widgets`, such as `../../ts/website_widgets` |
| `__app_page_module__`, `__AppPageClass__` | the two halves of `app_page_class`, in `page.py.tmpl` |

Copy the package's template to start an override, so it keeps the placeholders the command fills.
