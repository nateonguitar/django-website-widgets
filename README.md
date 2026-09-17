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
    def base_template_path(self) -> str:
        return 'website/templates/base.html'

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

        # Construct widgets (don't call .html() - framework does that)
        self.context.children['profile_card'] = ProfileCard(user=user)
```

Pages:
- Define `base_template_path()` for the wrapper template
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

## Templates

A widget's template sits next to its Python file and shares its name: `my_widget.py` renders
`my_widget.html`. Override `template_path()` to use a different file.

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
WidgetCompositionPage
  cards: [
    InfoCard(First Card)
    InfoCard(Second Card)
    InfoCard(Third Card)
  ]
  appbar:
    ExampleAppbar
      title: AppbarTitle(Widget Composition)
  footer:
    ExampleFooter
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

## License

MIT
