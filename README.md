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

    async def set_context(self, *args, **kwargs):
        # Construct widget - system will render it automatically
        self.context.children['appbar'] = Appbar(parent=self)
```

4. Create a widget and a `template.html` file next to it:

`website/widgets/project_details_card/project_details_card.py`
```python
from website_widgets import Widget
from project.models import Project

class ProjectDetailsCard(Widget):
    """Widget that displays project details."""

    def __init__(self, project: Project, parent: 'Widget | None' = None):
        super().__init__(parent=parent)
        self.context.data['project'] = project

    def html(self):
        """Renders the widget. Can be sync or async - system auto-detects."""
        return self.render_html()
```

`website/widgets/project_details_card/template.html`
```html
<div class="project-details-card">
    <p>Name: {{ data.project.name }}</p>
</div>
```

5. Create a page and a `template.html` file next to it:

`website/pages/project_page/project_page.py`
```python
from project.models import Project
from website.app_page import AppPage
from website.widgets.project_details_card import ProjectDetailsCard

class ProjectPage(AppPage):
    """Page that displays a single project."""

    def __init__(self, pk: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pk = pk

    async def set_context(self, *args, **kwargs):
        await super().set_context(*args, **kwargs)

        project = await Project.objects.aget(pk=self.pk)
        self.context.page['title'] = f'Project - {project.name}'
        self.context.data['project'] = project

        # Construct widgets - system will render them automatically
        self.context.children['project_details_card'] = ProjectDetailsCard(
            project=project,
            parent=self
        )
```


`website/pages/project_page/template.html`
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
- Accept data via constructor parameters
- Store data in `self.context.data` for templates
- Store child widget instances in `self.context.children`
- Implement `html()` method (can be sync or async - system auto-detects)

**Example:**
```python
class InfoCard(Widget):
    def __init__(self, title: str, content: str, parent: 'Widget | None' = None):
        super().__init__(parent=parent)
        self.context.data['title'] = title
        self.context.data['content'] = content

    def html(self):  # Or: async def html(self)
        return self.render_html()
```

Widgets can:
- Accept any parameters in `__init__()`
- Store child widgets (not HTML) in `self.context.children`
- Access request via `self.request`
- Access request user via `self.request.user`
- Use either `def html()` or `async def html()` - framework detects automatically

### Page

Extends `Widget` and represents a full page.

**Key Pattern:**
- URL parameters are passed to `__init__()` and stored as instance variables
- Use `set_context()` to load data and construct child widgets
- Child widgets are stored as objects, not HTML
- Framework automatically renders the widget tree after `set_context()`

**Example with URL parameters:**
```python
class ProfilePage(AppPage):
    def __init__(self, username: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.username = username

    async def set_context(self, *args, **kwargs):
        await super().set_context(*args, **kwargs)
        user = await User.objects.aget(username=self.username)
        self.context.page['title'] = f'Profile: {user.username}'

        # Construct widgets (don't call .html() - framework does that)
        self.context.children['profile_card'] = ProfileCard(user=user, parent=self)
```

Pages:
- Define `base_template_path()` for the wrapper template
- Receive URL parameters in `__init__()`
- Use `set_context()` to load data and construct child widgets
- Register with Django URLs via `.as_view()`
- Have lifecycle hooks for authentication, permissions, etc.

### Context

Each widget has `self.context` with:
- `data`: Dictionary for template variables
- `children`: Dictionary for child widget instances (Widget objects or lists)
- `page`: Page-level data (title, meta tags, etc.) shared across all widgets

**Important:** Store Widget instances in `children`, not HTML strings. The framework automatically converts them to HTML after the widget tree is built.

## Templates

Create a `template.html` next to the widget/page class:

```html
<div class="my-widget">
    <h1>{{ data.title }}</h1>
    {{ children.my_widget }}
</div>
```

## Configuration

Configure django-website-widgets in your `settings.py`:

```python
from website_widgets.config import WebsiteWidgetsConfig

WEBSITE_WIDGETS = WebsiteWidgetsConfig(
    show_debug_tree=True,  # Show widget tree visualization on pages (default: False)
)
```

If `WEBSITE_WIDGETS` is not defined, a default configuration is used automatically.

### Debug Tree Visualization

Enable `show_debug_tree=True` to display a visual representation of your widget hierarchy at the bottom of each page. This is useful during development to understand the structure of your widget tree.

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
    def __init__(self, title: str, content: str, parent: 'Widget | None' = None):
        super().__init__(parent=parent)
        self._debug_label = title  # Shows as "InfoCard(My Title)" in debug tree
        self.context.data['title'] = title
        self.context.data['content'] = content
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
