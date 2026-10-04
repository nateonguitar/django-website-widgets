# Django Website Widgets

A reusable Django app for building component-based web interfaces with widgets and pages.

## Installation

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

2. Create a base.html for all pages to use (customize as needed with stylesheets, an appbar header, a footer, etc.)

`website/templates/base.html`
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
            {{ main_content_html }}
        </main>
    </body>
</html>

```

3. Create subclass Page for reusing across all other pages

`website/app_page.py`
```python
from website_widgets import Page
from website.widgets.appbar import Appbar

class AppPage(Page):
    base_template_path = 'templates/base.html'

    async def set_context(self):
        # Construct widget - system will render it automatically
        self.context.children['appbar'] = Appbar()
```

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
- Set `base_template_path` for the wrapper template
- Receive URL parameters in `__init__()`
- Use `set_context()` to load data and construct child widgets
- Register with Django URLs via `.as_view()`
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
widget.context.page['nonce'] = nonce
html = await widget.render__standalone(request)
```

Tests render a widget directly against a mock request, optionally as a given user:

```python
html = await ProjectListTile(project=project).render__test(user=user)   # async def test
html = ProjectListTile(project=project).render__test_sync(user=user)    # def test
```

Each runs the widget's `set_context()` and every descendant's, then the templates. No base
template wraps the result.

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

A page's layout is the one template set by path: `base_template_path` names a file shared by every
page, so it lives in a common folder rather than beside any one of them.

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

## Example Site

`website_widgets.example` is a small demo site. Every page renders on the server, and each of its
three parts has its own base page and stylesheet:

- **The index** links the two apps.
- **The projects app** is a project tracker with a fake login and an appbar. Inline JavaScript
  calls JSON endpoints to log in and out and to create, edit and delete projects. Its base page
  shows access-denied and not-found variants, and its login page a logged-in variant.
- **The advanced demo** has no login: composition, async widgets (awaited one after another
  versus gathered by their parent), a widget rendered by an endpoint with
  `render__standalone()` and added under one rendered with the page, and a conditional (304)
  response.

Its tests include widget tests using `render__test_sync()`.

Install it for development only, and mount its URLs:

```python
# settings.py
if DEBUG:
    INSTALLED_APPS.append('website_widgets.example')

# urls.py
from django.apps import apps

if apps.is_installed('website_widgets.example'):
    urlpatterns.append(path('website-widgets-example/', include('website_widgets.example.urls')))
```

Then open `/website-widgets-example/`. In the projects app, log in as `user_1`, `user_2` or
`admin` with any password.

**The prefix is yours to choose.** The library ships only the routes beneath it; every link,
form target and endpoint URL in the example is built with `{% url %}` or `reverse()`, so any
prefix works, the site root included. `website-widgets-example/` is the suggested one, since it
can't collide with the host project's own pages. Its URL names are all
`website_widgets_example_<name>` (`website_widgets_example_projects`, ...) for the same reason.

**The projects app's data lives only in memory.** The users and projects are Python objects
seeded when the app loads, so they are wiped whenever the Django server restarts, autoreloads
included. Behind a load
balancer or with several server processes, each process holds its own copy, so what a request sees
depends on which process serves it. The login is a plain cookie holding a user id, not
authentication.

Its endpoints are plain Django returning `JsonResponse`, one endpoint (one method on one URL) per
file in `api/` folders that mirror the URLs, such as `projects/api/projects/by_id/patch.py`.
`Endpoint.route()` builds the view a URL pattern points at from the endpoints sharing that
URL. Each endpoint reads its input into a request DTO beside it (`ProjectCreateDto.from_dict()`,
then `validate()`), builds or changes the model from that (`Project.from_create_dto()`), and
returns a response DTO's `to_dict()`, as a Ninja or DRF schema would. The library doesn't care how
endpoints are built, so Django Ninja, Django REST Framework or pydantic work the same way. Its tests, in
`website_widgets/example/tests/`, mount the example URLs themselves, so they run whether or not
the app is installed.

## Management Commands

Check installation:
```bash
python manage.py test_website_widgets --verbose
```

## License

MIT
