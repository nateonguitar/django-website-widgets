# Django Website Widgets

A reusable Django app for building component-based web interfaces with widgets and pages.

A widget can also render on its own into the Django you already have: an ordinary view and
template, an email, the admin. So a site can adopt widgets one piece at a time, with no `WebPage`
and no build step.

## Examples

The repository's [`examples/`](https://github.com/nateonguitar/django-website-widgets/tree/main/examples)
folder holds small Django projects you can run, each showing one part of the library: pages and
widgets, requests and routing, widgets in plain Django views, an email and the admin, and a small
project tracker using all of it. They aren't installed with the package; clone the repository,
`cd` into one, then `poetry install`, `migrate` and `runserver`.
[`examples/README.md`](https://github.com/nateonguitar/django-website-widgets/blob/main/examples/README.md)
lists them all. [Gametabs](https://gametabs.net) is a real site built on it.

## Documentation

This README introduces the library. How each part works, and why, is in the docs that ship
inside the package, indexed by
[`website_widgets/AGENTS.md`](https://github.com/nateonguitar/django-website-widgets/blob/main/website_widgets/AGENTS.md):

- [`rendering_pipeline.md`](https://github.com/nateonguitar/django-website-widgets/blob/main/website_widgets/docs/rendering_pipeline.md): how a request becomes HTML, and rendering a widget outside a page
- [`routing.md`](https://github.com/nateonguitar/django-website-widgets/blob/main/website_widgets/docs/routing.md): `@register_url`, route discovery and ordering
- [`frontend_controllers.md`](https://github.com/nateonguitar/django-website-widgets/blob/main/website_widgets/docs/frontend_controllers.md): the TypeScript `Controller`, `App` and `Completer`
- [`reverse_template.md`](https://github.com/nateonguitar/django-website-widgets/blob/main/website_widgets/docs/reverse_template.md): URL templates for the frontend
- [`creating_and_upgrading_an_app.md`](https://github.com/nateonguitar/django-website-widgets/blob/main/website_widgets/docs/creating_and_upgrading_an_app.md): `ww_create_app` and `ww_upgrade`, and the framework's TypeScript and these docs copied into a project
- [`creating_pages_and_widgets.md`](https://github.com/nateonguitar/django-website-widgets/blob/main/website_widgets/docs/creating_pages_and_widgets.md): `ww_create_page` and `ww_create_widget`, and overriding their templates
- [`npm_watch.md`](https://github.com/nateonguitar/django-website-widgets/blob/main/website_widgets/docs/npm_watch.md): starting `npm run watch` with `runserver`

`AGENTS.md` is written for AI coding assistants as well as people: an index plus the rules
every change follows.

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

3. Create a `WebPage` subclass for every other page to extend, pointing at that template:

`website/app_page.py`
```python
import os

from website_widgets import WebPage
from website.widgets.appbar import Appbar

class AppPage(WebPage):
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
- Can be sync or async - use `async def set_context(self):` only when awaiting. A page renders
  in an async view, so database access in a sync `set_context()` there raises
  `SynchronousOnlyOperation`; use the async ORM. A widget rendered with `render()` from sync code
  is the reverse: it must use `def`, and the sync ORM works

### WebPage

Extends `Widget` and represents a full page answering a web request. (The name keeps it apart
from Django's paginator `Page`.)

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

A widget doesn't need a `WebPage`. `render()` returns its HTML as `SafeText`, so it drops into any
ordinary Django template, and a project can adopt widgets piece by piece without converting its
views. Construct the widget, adjust it, and render it once:

```python
from django.shortcuts import render


def project_list(request):
    tiles = []
    for project in Project.objects.all():
        widget = ProjectListTile(project=project)
        # Provide any custom values the widget might need.
        widget.context.page['foo'] = bar
        tiles.append(widget.render(request))
    return render(request, 'projects/list.html', {'tiles': tiles})
```

```django
{% extends 'base.html' %}
{% block content %}
  {% for tile in tiles %}{{ tile }}{% endfor %}
{% endblock %}
```

`render()` runs with no event loop, so its widgets use plain `def set_context()` and the sync
ORM; it raises on an `async def set_context()`. The request is optional: an email body or an
admin hook has none, and a widget that reads `self.request` without one raises rather than
getting a fake. The `03_widgets_in_plain_django` [example](#examples) has all three: a
traditional view and template, emails and an admin tool.

In async code, such as an endpoint returning HTML fragments for an infinite scroller, await
`arender()` instead. It runs sync and async `set_context()`s alike, as a page does:

```python
html = await ProjectListTile(project=project).arender(request)
```

A widget's template can be a whole document. An HTML email is a widget holding what every email
repeats, the `<head>`, a header and a footer, with the email's own part passed in as a child:

```python
html = EmailDocument(subject='Welcome', content=WelcomeMessage(user=user)).render()
```

Tests render a widget against a mock `GET /`, optionally as a given user:

```python
html = ProjectListTile(project=project).render__test(user=user)          # def test
html = await ProjectListTile(project=project).arender__test(user=user)   # async def test
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

Pages are found by importing every module under the website app's `pages/` folder, and their
routes reverse as `website:<name>`, the name defaulting to the class name. Routes are tried most
specific first, never in file order, so `profile/settings` always beats
`profile/<str:username>`. `python manage.py ww_show_routes` lists them in that order
and checks that each reaches its page. Routing a page by hand with `MyPage.as_view()` still
works, and the two mix freely. See
[`docs/routing.md`](https://github.com/nateonguitar/django-website-widgets/blob/main/website_widgets/docs/routing.md)
for discovery, the ordering rule, the tie check and the command's options.

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
script prefix apply as they do in `reverse()`. See
[`docs/reverse_template.md`](https://github.com/nateonguitar/django-website-widgets/blob/main/website_widgets/docs/reverse_template.md)
for `paramnames`, which a `re_path()` with unnamed groups needs.

### Starting the frontend watcher with `runserver`

A project that builds its frontend with npm can start `npm run watch` whenever Django's
development server starts. Call `start_npm_watch()` in `manage.py`, after
`DJANGO_SETTINGS_MODULE` is set:

```python
from website_widgets import start_npm_watch


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    start_npm_watch()
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
```

It acts only on `runserver`, and runs `npm run watch` in the folder of the app named by
`website_app_name`, once per folder: not again when the autoreloader restarts the server, and
not when one is already running there. See
[`docs/npm_watch.md`](https://github.com/nateonguitar/django-website-widgets/blob/main/website_widgets/docs/npm_watch.md)
for how it tells watchers apart.

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
shared by every page, so it lives beside the shared `WebPage` subclass rather than beside any one page.

Override `get_template_path()` when the choice needs more than an attribute.

```html
<div class="my-widget">
    <h1>{{ data.title }}</h1>
    {{ children.my_widget }}
</div>
```

Templates are opened directly rather than through Django's template loader, so context processors
do not run. The context holds only `request`, `user`, `page`, `data` and `children`. See
[`docs/rendering_pipeline.md`](https://github.com/nateonguitar/django-website-widgets/blob/main/website_widgets/docs/rendering_pipeline.md)
for the full render order.

## Configuration

Configure django-website-widgets in your `settings.py`:

```python
from website_widgets.config import GenerateComponentConfig, WebsiteWidgetsConfig

WEBSITE_WIDGETS = WebsiteWidgetsConfig(
    show_debug_tree=True,  # Show widget tree visualization on pages (default: False)
    website_app_name='website',  # Label of the app holding pages/ and package.json (default: 'website')
    generate_component=GenerateComponentConfig(
        # Dotted path of a generated page's base class (default: '<website_app_name>.pages.app_page.AppPage')
        app_page_class='website.pages.app_page.AppPage',
        # Your own generator templates, each replacing the package's of the same name (default: None)
        templates_dir=BASE_DIR / 'website' / 'generator_templates',
    ),
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

Every command is prefixed `ww_`.

Create the website app, named by `WEBSITE_WIDGETS.website_app_name` (`website` by default), with
the framework's TypeScript (`App`, `Controller`, `Completer`) and the package's docs in its
`ts/website_widgets/`. It lists every file and asks before writing:
```bash
python manage.py ww_create_app
```

After every upgrade of the package, bring that folder up to the installed version (and run it
once on a website app that never ran `ww_create_app`):
```bash
python manage.py ww_upgrade
```
It overwrites only the files the package ships, deletes ones it no longer ships, and leaves
anything else in the folder alone. Commit the folder, so an upgrade shows up as a diff. A system
check warns when the folder is from another version than the installed package. Both commands
offer to point your `CLAUDE.md`, `.claude/CLAUDE.md` or `AGENTS.md` at the copied docs. See
[`docs/creating_and_upgrading_an_app.md`](https://github.com/nateonguitar/django-website-widgets/blob/main/website_widgets/docs/creating_and_upgrading_an_app.md).

Create a page or widget, with an optional TypeScript controller and stylesheet registered in
`ts/main.ts` (each asks when a flag is left out):
```bash
python manage.py ww_create_widget like_button --tscontroller=true --stylesheet=true
python manage.py ww_create_page profile_page --tscontroller=false --stylesheet=false
```
They need the framework folder, and for a page, the base class at
`GenerateComponentConfig.app_page_class`. A project overrides any of their templates with its
own, in `templates_dir`. See
[`docs/creating_pages_and_widgets.md`](https://github.com/nateonguitar/django-website-widgets/blob/main/website_widgets/docs/creating_pages_and_widgets.md).

List the `@register_url` routes in the order they are tried, and check each reaches its page
(see "Routing pages with `@register_url`"):
```bash
python manage.py ww_show_routes
python manage.py ww_show_routes --columns=url,name,page,reaches_page --path-param-type=type
```

## License

MIT
