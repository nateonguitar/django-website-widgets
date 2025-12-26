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

1. Add to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    ...
    'website_widgets',
]
```

2. Create a widget:

```python
from website_widgets import Widget
from django.utils.safestring import SafeText

class MyWidget(Widget):
    async def html(self, title: str) -> SafeText:
        self.context.data['title'] = title
        return self.render_html(self.template_path())
```

3. Create a page:

```python
from website_widgets import Page

class MyPage(Page):
    def base_template_path(self) -> str:
        return 'path/to/base.html'

    async def set_context(self, *args, **kwargs):
        widget = MyWidget(parent=self)
        self.context.children['my_widget'] = await widget.html('Hello World')
```

4. Register in `urls.py`:

```python
from django.urls import path
from .pages.my_page import MyPage

urlpatterns = [
    path('my-page/', MyPage.as_view(), name='my_page'),
]
```

## Core Concepts

### Widget

Base class for reusable UI components. Widgets can:
- Accept parameters via `html()` method
- Store data in `self.context.data` for templates
- Store child widgets in `self.context.children`
- Access request via `self.request`

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

Create a `template.html` next to your widget/page class:

```html
<div class="my-widget">
    <h1>{{ title }}</h1>
    {{ my_widget }}
</div>
```

## Management Commands

Check installation:
```bash
python manage.py test_website_widgets --verbose
```

## License

MIT
