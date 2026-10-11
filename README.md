# Django Website Widgets

A reusable Django app for building component-based web interfaces with widgets and pages.

## Installation

Requires Python 3.12+ and Django 5.2+.

```bash
pip install django-website-widgets
```

Or with Poetry:

```bash
poetry add django-website-widgets
```

## Quick Start

1. Add to `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    ...
    'website_widgets',
]
```

2. Create a document template for all pages to use: the whole HTML document, `<head>` included.
   Customize it as needed with stylesheets, an appbar, a footer, etc.

`website/document_template.html`
```html
{% load static %}
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ page.title|default:"Foo" }}</title>
        <link rel="stylesheet" href="{% static 'styles.css' %}">
    </head>
    <body>
        {{ children.appbar }}

        <main id="main-content">
            {{ page_content_html }}
        </main>
    </body>
</html>

```

3. Create a `Page` subclass for every other page to extend, pointing at that template:

`website/app_page.py`
```python
import os

from website_widgets import Page
from website.widgets.appbar import Appbar

class AppPage(Page):
    # Absolute: a relative path resolves beside each concrete page, not beside this file.
    document_template_path = os.path.join(os.path.dirname(__file__), 'document_template.html')

    async def set_context(self):
        # Construct widget - system will render it automatically
        self.context.children['appbar'] = Appbar()
```

A page renders two templates against the same context: its own, then the document template, which
receives the first as `{{ page_content_html }}`. So `children.appbar` can render in either one.
Here it sits outside the page's content but still reads `context.page`, which every page fills
before either template renders:

`website/widgets/appbar/appbar.html`
```html
<header class="appbar">
    <a href="/">Home</a>
    <span>{{ page.title }}</span>
</header>
```

Where the appbar goes is the project's choice: every page can set its own
`children['appbar']`, a page can leave it out, or the document template can hold the markup
directly.

4. Create a widget and a template next to it, named after the widget's Python file:

`website/widgets/project_details_card/project_details_card.py`
```python
from website_widgets import Widget
from project.models import Project

class ProjectDetailsCard(Widget):
    """Widget that displays project details."""

    def __init__(self, project: Project):
        super().__init__()
        self.context.data['project'] = project

    def set_context(self):
        """Called before rendering. Can be sync or async."""
        super().set_context()
```

`website/widgets/project_details_card/project_details_card.html`
```html
<div class="project-details-card">
    <p>Name: {{ data.project.name }}</p>
</div>
```

5. Create a page and its template the same way:

`website/pages/project_page/project_page.py`
```python
from project.models import Project
from website.app_page import AppPage
from website.widgets.project_details_card import ProjectDetailsCard

class ProjectPage(AppPage):
    """Page that displays a single project."""

    def __init__(self, pk: int):
        super().__init__()
        self.pk = pk

    async def set_context(self):
        await super().set_context()

        project = await Project.objects.aget(pk=self.pk)
        self.context.page['title'] = f'Project - {project.name}'
        self.context.data['project'] = project

        # Construct widgets - system will render them automatically
        self.context.children['project_details_card'] = ProjectDetailsCard(
            project=project
        )
```


`website/pages/project_page/project_page.html`
```html
<div id="project-details-page">
    {{ children.project_details_card }}

    <p>Other content here</p>
</div>
```

6. Register in `urls.py`:

```python
from django.urls import path
from .pages.project_page import ProjectPage

urlpatterns = [
    path('project/<int:pk>', ProjectPage.as_view(), name='project_page'),
]
```

## Core Concepts

### Widget

Base class for reusable UI components. Uses a declarative, constructor-based pattern similar to Flutter or React.

**Key Pattern:**
- Accept data via `__init__()` parameters
- Store data on instance variables
- Implement `set_context()` to populate `self.context.data` and create child widgets
- System automatically renders widgets after initialization

**Example:**
```python
class InfoCard(Widget):
    def __init__(self, title: str, content: str):
        super().__init__()
        self.title = title
        self.content = content

    def set_context(self):
        self.context.data['title'] = self.title
        self.context.data['content'] = self.content
```

Widgets:
- Accept data parameters in `__init__()` and store them
- Use `set_context()` to create child widgets (Widget objects or lists)
- Store children in `self.context.children` - system renders them
- Access `self.request` and `self.request.user` from `set_context()` onwards (not in `__init__()`)
- Can be sync or async - use `async def set_context(self):` only when awaiting. Rendering always
  runs in an async view, so database access in a sync `set_context()` raises
  `SynchronousOnlyOperation`; use the async ORM

### Page

Extends `Widget` and represents a full page.

**Key Pattern:**
- URL parameters passed to `__init__()` - store them on self
- `set_context()` loads data and creates child widgets
- Assign Widget objects (or lists) to `self.context.children`
- System calls `set_context()` recursively, then renders all widgets

**Example with URL parameters:**
```python
class ProfilePage(AppPage):
    def __init__(self, username: str):
        super().__init__()
        self.username = username

    async def set_context(self):
        await super().set_context()
        user = await User.objects.aget(username=self.username)
        self.context.page['title'] = f'Profile: {user.username}'

        # Construct widgets; the page renders them
        self.context.children['profile_card'] = ProfileCard(user=user)
```

Pages:
- Set `document_template_path` for the HTML document wrapping their own template
- Receive URL parameters in `__init__()`
- Use `set_context()` to load data and construct child widgets
- Route with `@register_url` (see below), or by hand in `urls.py` with `.as_view()`
- Override `handle_request()` for authentication, redirects or conditional responses, and
  `build_response()` for headers

### WidgetContext

Each widget has `self.context`, a `WidgetContext`, with:
- `data`: Template variables (dict)
- `children`: Child widgets - values can be Widget, list[Widget], or None
- `page`: Shared page-level data (title, meta, etc.)

System renders widgets to HTML automatically. Lists iterate in templates via `{% for item in children.items %}`.

### Rendering a widget on its own

Outside a page, for an endpoint returning HTML fragments (an infinite scroller, a "load more"
button), construct the widget, adjust it, and render it once:

```python
widget = ProjectListTile(project=project)
# Provide any custom values the widget might need.
widget.context.page['foo'] = bar
html = await widget.render__standalone(request)
```

Tests render a widget directly against a mock request, optionally as a given user:

```python
html = await ProjectListTile(project=project).render__test(user=user)   # async def test
html = ProjectListTile(project=project).render__test_sync(user=user)    # def test
```

Each runs the widget's `set_context()` and every descendant's, then the templates. No document
template wraps the result.

### Routing pages with `@register_url`

A page can declare its own routes instead of being listed in `urls.py`. The decorator takes
`path()`'s arguments, and stacks one per route:

```python
from website_widgets import register_url

@register_url('')
class HomePage(AppPage): ...

@register_url('forum/<int:post_id>', name='forum_post')
@register_url('tab-requests/<int:post_id>', name='tab_request')
class ForumPostPage(AppPage): ...

@register_url('forum/create-post', name='forum_create_post', kwargs={'post_type': 'forum_post'})
class ForumCreatePostPage(AppPage): ...
```

Then include every decorated page with one line, the way the admin is included:

```python
from website_widgets import PageRoutes

urlpatterns = [
    path('', PageRoutes.urls()),
    ...
]
```

- **Pages are found by importing every module under the website app's `pages/` folder**, the app
  being `WebsiteWidgetsConfig.website_app_name` (default `'website'`). A page elsewhere isn't found.
- **Routes live in a namespace named after that app.** `name` defaults to the class name, so
  `HomePage` reverses as `reverse('website:HomePage')`, and `forum_post` as `'website:forum_post'`.
- **`kwargs` reach the page's constructor** alongside the URL's parameters.
- **Routes are tried most specific first, never in file order.** They are compared segment by
  segment: a fixed segment comes before `int`, then `uuid`, `slug`, `str` and `path`, and equally
  specific routes fall back to alphabetical order. So `profile/settings` is always tried before
  `profile/<str:username>`, wherever either is declared.
- **Two equally specific routes that can match the same URL fail a system check**
  (`website_widgets.E001`), such as `a/<str:x>` and `a/<str:y>`.
- **A decorated route is an ordinary `path()`.** `reverse()`, `{% url %}`, `resolve()` and URL
  tools such as django-extensions' `show_urls` all see it. Routing a page by hand with
  `path('...', MyPage.as_view(), name='...')` still works, and the two mix freely; a hand-routed
  page's name sits outside the namespace.

To see the order routes are tried in, and check that nothing clobbers them, run
`show_page_resolve_order`:

```
$ python manage.py show_page_resolve_order
#   URL                                              Segments  Page
1   /moderation/reports/<int:report_id>              f/f/i     ViewReportPage
...
15  /profile/<str:username>                          f/s       UserProfilePage
...
17  /                                                f         HomePage

Segments: f fixed, i int, s str, g slug, u uuid, p path, and a project converter by its name.
All 37 page routes reach their page.
```

For each route it reverses a sample URL (`/profile/a`) and resolves it through the whole project,
so it also catches a route that never reaches its page because something earlier in `urls.py`
takes its URLs, such as a hand-written route or a catch-all, or because `PageRoutes.urls()` isn't
included. A route that fails prints in red with the reason, and the command exits non-zero, so it
can run in CI.

- `--columns` picks the columns after `#`, in order, from `url,segments,name,page,reaches_page`
  (default `url,segments,page`). The reachability check runs either way.
- `--path-param-type` shows a path parameter as declared (`full`, the default:
  `<str:game_slug>`), as its converter (`type`: `<str>`) or as the sample value the check uses
  (`example`: `a`).

### URL templates for the frontend

`reverse_template()` stands in for `reverse()` when the frontend fills in the parameters. It
reverses a URL name into a template with a `{name}` placeholder per route parameter:

```python
from website_widgets import reverse_template

# path('projects/<int:project_id>/tasks/<slug:task_slug>', ..., name='project_task')
reverse_template('project_task')   # '/projects/{project_id}/tasks/{task_slug}'
reverse_template('project_list')   # '/projects', as reverse() returns it
```

Placeholders take the route's own parameter names, and namespaces, `include()` prefixes and the
script prefix apply as they do in `reverse()`. Converters don't run, so a placeholder is accepted
wherever a parameter goes. Pass `paramnames` to rename the placeholders in route order, which a
`re_path()` with unnamed groups needs: `reverse_template('legacy', ['legacy_id'])`. A name whose
routes take different parameters raises `ValueError` unless `paramnames` picks one by count.

## Templates

A widget's template sits next to its Python file and shares its name: `my_widget.py` renders
`my_widget.html`. Set `template_filename` to use a different file, either on the class or in
`set_context()` to pick between files at runtime.

**`template_filename` is a bare file name, never a path.** A template lives beside the code that
chooses it, so a `/`, a `\` or `..` raises `ValueError`. The file is looked up beside the class's
own `.py` file first, then beside each base class's file in inheritance order, and the first match
wins. That lets a base class keep a variant beside its own module and switch any subclass to it.
A name found nowhere raises `FileNotFoundError` listing every folder searched.

```python
class ProjectPage(AppPage):
    async def set_context(self):
        await super().set_context()
        project = await Project.objects.filter(pk=self.pk).afirst()
        if project is None:
            self.status_code = 404
            self.template_filename = 'project_page__not_found.html'
            return
        ...
```

**Suggested convention: name a variant `<module>__<variant>.html`**, with a double underscore,
beside the main template:

```
project_page/
    project_page.py
    project_page.html
    project_page__not_found.html
    project_page__archived.html
```

The double underscore marks where the module name ends, the way it separates the parts of a Django
lookup (`author__name__startswith`): module and variant names both contain single underscores, so
one alone can't. The prefix keeps every variant sorted next to the template it replaces, and an
editor tab or a search result names its component without the folder. Give the variant the same
root element as the main template, so the component's styles still apply to it.

A page's document template is the one template set by path: `document_template_path` names a file
shared by every page, so it lives beside the shared `Page` subclass rather than beside any one page.

Override `get_template_path()` when the choice needs more than an attribute.

```html
<div class="my-widget">
    <h1>{{ data.title }}</h1>
    {{ children.my_widget }}
</div>
```

Templates are opened directly rather than through Django's template loader, so context processors
do not run. The context holds only `request`, `user`, `page`, `data` and `children`. See
`docs/rendering_pipeline.md` for the full render order.

## Configuration

Configure django-website-widgets in your `settings.py`:

```python
from website_widgets.config import WebsiteWidgetsConfig

WEBSITE_WIDGETS = WebsiteWidgetsConfig(
    show_debug_tree=True,  # Show widget tree visualization on pages (default: False)
    website_app_name='website',  # Label of the app holding your pages/ (default: 'website')
)
```

If `WEBSITE_WIDGETS` is not defined, a default configuration is used automatically. The setting is
read once per process, so changing it at runtime has no effect.

### Debug Tree Visualization

Enable `show_debug_tree=True` to display a visual representation of your widget hierarchy after each page's main content. This is useful during development to understand the structure of your widget tree.

**Example output:**
```
CompositionPage
  stylesheet:
    AdvancedStylesheet
  constructor_card:
    InfoCard
  list_cards: [
    InfoCard
    InfoCard
    InfoCard
  ]
  skipped_card: None
  page_title_note:
    PageTitleNote
```

#### Adding Debug Labels

For better debugging, add a `_debug_label` to your widgets:

```python
class InfoCard(Widget):
    def __init__(self, title: str, content: str):
        super().__init__()
        self._debug_label = title  # Shows as "InfoCard(My Title)" in debug tree
        self.title = title
        self.content = content
```

Without `_debug_label`, widgets display only their class name (e.g., `InfoCard`). With the label, they display as `InfoCard(My Title)`, making it easier to identify specific widget instances in complex trees.

**Recommendation:** Only enable `show_debug_tree` in development environments, not in production.

## Management Commands

Check installation:
```bash
python manage.py test_website_widgets --verbose
```

List the `@register_url` routes in the order they are tried, and check each reaches its page
(see "Routing pages with `@register_url`"):
```bash
python manage.py show_page_resolve_order
python manage.py show_page_resolve_order --columns=url,name,page,reaches_page --path-param-type=type
```

## License

MIT
