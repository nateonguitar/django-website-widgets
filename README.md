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

class AppPage(Page):
    def base_template_path(self) -> str:
        return 'website/templates/base.html'

    async def set_context(self, *args, **kwargs):
        self.context.children['appbar'] = ExampleAppbar(parent=self).html_sync()
```

4. Create a widget and a `template.html` file next to it:

`website/widgets/project_details_card/project_details_card.py`
```python
from website_widgets import Widget

class ProjectDetailsCard(Widget):
    def html_sync(self, project: Project):
        self.context.data['project'] = project
        return self.render_html()
```

`website/widgets/project_details_card/template.py`
```html
<div class="project-details-card">
    <p>Name: {{ data.project.name }}</p>
</div>
```

5. Create a page and a `template.html` file next to it:

`website/pages/project_page/project_page.py`
```python
from project.models import Project
from website_widgets import Page

class ProjectPage(AppPage):
    async def set_context(self, pk, *args, **kwargs):
        await super().set_context(*args, **kwargs)
        project = await Project.objects.aget(pk=pk)
        self.context.page['title'] = f'Project - {project.name}'
        self.context.data['project'] = project
        self.context.children['project_details_card'] = ProjectDetailsCard(parent=self).html_sync(project)
```


`website/widgets/project_page/template.py`
```html
<div id="project-details-page">
    {{ children.project_details_card }}

    <p>Other</p>
</div>
```

5. Register in `urls.py`:

```python
from django.urls import path
from .pages.project_page import ProjectPage

urlpatterns = [
    path('project/<int:pk>', ProjectPage.as_view(), name='project_page'),
]
```

## Core Concepts

### Widget

Base class for reusable UI components.

Widgets can:
- Accept parameters
  - When the widget needs to do async work
    - `async def html(project_id: int)`
  - When the widget will not do async work
    - `def html_sync(project: Project)`
- Store data in `self.context.data` for templates
- Store child widgets in `self.context.children`
- Access request via `self.request`
- Access request user via `self.user`

### Page

Extends `Widget` and represents a full page. Pages:
- Define `base_template_path()` for the wrapper template
- Use `set_context()` to load data and create child widgets
- Register with Django URLs via `.as_view()`
- Have lifecycle hooks for authentication, permissions, etc.

### Context

Each widget has `self.context` with:
- `data`: Dictionary for template variables
- `children`: Dictionary for child widget HTML
- `page`: Page-level data (title, meta tags, etc.)

## Templates

Create a `template.html` next to the widget/page class:

```html
<div class="my-widget">
    <h1>{{ data.title }}</h1>
    {{ children.my_widget }}
</div>
```

## Management Commands

Check installation:
```bash
python manage.py test_website_widgets --verbose
```

## License

MIT
