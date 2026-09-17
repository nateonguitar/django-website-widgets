# The Rendering Pipeline

What happens between a request arriving at a `Page` and HTML going back out: the order the widget
tree is built and rendered in, what a template can see, and where the async boundary sits. The
README covers the shapes of `Widget`, `Page` and `WidgetContext`; this covers the order things run
in, which is where the surprises are. Read this before overriding `handle_request()` or
`build_response()`, or when a widget renders but its content is missing.

Primary code:
- `website_widgets/page.py` — `Page.as_view()`, `handle_request()`, `build_response()`
- `website_widgets/widget.py` — `_initialize_widget_tree()`, `_render_children_to_html()`,
  `template_path()`, `_context_dict()`, `render_html()`
- `website_widgets/widget_context.py` — `WidgetContext`
- `website_widgets/config.py` — `WebsiteWidgetsConfig`, `get_config()`

## One instance per request

`Page.as_view()` is a factory, not Django's class-based view. It returns an `async def` view that,
for each request, constructs a **fresh page instance**, assigns `_request` (read as
`self.request`), and calls `handle_request()`, awaiting it if it is a coroutine.

URL parameters are passed to **both** the constructor and `handle_request()`. That is what lets a
page keep them as instance attributes:

```python
class ProfilePage(Page):
    def __init__(self, username: str):
        super().__init__()
        self.username = username
```

Arguments given to `as_view()` itself go to the constructor only, after the URL's positional
arguments.

Because the instance is per-request, instance state is safe. Class-level mutable state is not: it
is shared across every request in the process.

The default `handle_request()` calls the page's own `set_context()`, then `build_response()`. Every
other widget's `set_context()` runs later, inside `build_response()`.

## `build_response()` runs the tree in four passes

```
1. await self._initialize_widget_tree()    every descendant's set_context()
2. self._generate_debug_tree()             only if show_debug_tree is on
3. await self._render_children_to_html()   every descendant's render_html()
4. self.html(), then the base template     the page's own template, then the wrapper
```

**Pass 1 is depth-first and parent-before-child.** For each child widget the tree walker assigns
`_request`, **shares `context.page` by reference**, calls `set_context()` (awaiting it only if it
is a coroutine function), and then recurses into that widget's own children. So a widget's
`set_context()` may freely construct more children; they are initialized on the way down.

The ordering consequence that catches people: **a parent's `set_context()` has already returned
before any child's runs.** A parent cannot read a child's `context.data`. Data flows down through
constructor arguments, never up.

**Pass 3 replaces the widgets with their HTML.** `_render_children_to_html()` renders children
before their parent and then overwrites `self.context.children`: the dict's values stop being
`Widget` objects and become `SafeText`. After this pass, `context.children` is no longer a tree.

A child value may be a `Widget`, a `list[Widget]`, or `None`:

| Value in `context.children` | Pass 1 | Pass 3 |
|---|---|---|
| `Widget` | initialized | rendered to `SafeText` |
| `list` of `Widget` | each initialized | rendered to a list of `SafeText` |
| `list` containing a non-`Widget` | `TypeError` | `TypeError` |
| `None` | skipped | stays `None` |
| anything else | silently skipped | `TypeError` |

A list is iterated in the template with `{% for item in children.items %}`.

Pass 2 sits between 1 and 3 because it needs both: the tree must be fully constructed to be worth
drawing, and the children must still *be* widgets, since the debug tree reports class names and
each widget's optional `_debug_label`.

## The page's own rendering

`self.html()` returns `self.render_html()`, which renders the page's own template. The result, or
`self._override_main_content_html` if that attribute is set, has the debug tree appended when one
was generated, and is then passed into the template at `base_template_path()` as
`main_content_html`.

`base_template_path()` raises `NotImplementedError` on `Page` itself. The usual pattern is one
intermediate subclass per project that returns the app's base template, with individual pages
inheriting it.

`_override_main_content_html` is the escape hatch for replacing a page's body while keeping the
wrapper, for an error state say. Set it before `build_response()` runs and the page's own template
is not rendered at all.

The response is `HttpResponse(html, status=self.status_code)`. `status_code` is a plain class
attribute on `Page`, defaulting to `200`; assign it before `build_response()` to change it.

## Templates bypass Django's loader

`render_html()` opens the template file with `open()`, builds a `Template` from the string, and
renders it against a bare `Context`. Three consequences, all easy to get wrong:

**No template context processors run.** The context is exactly five keys, assembled in
`_context_dict()`:

| Key | Value |
|---|---|
| `request` | `self.request` |
| `user` | `self.request.user` |
| `page` | `self.context.page`, shared by reference down the whole tree |
| `data` | `self.context.data`, this widget only |
| `children` | `self.context.children`, this widget only |

Anything a project expects from a context processor (`csrf_token`, `MEDIA_URL`, `debug`, settings
exposed globally) **is not there** and resolves to empty with no error. `{% load %}`, custom tags
and filters, `{% url %}` and `{% static %}` all work normally; only the automatic context is
absent. The base template additionally receives `main_content_html`, through `render_html()`'s
`extra_context` argument; that argument exists for the library's own use, and application code
puts values in `self.context.data`.

**`data` and `children` are per-widget, `page` is shared.** A child cannot see its parent's `data`.
Anything every widget must reach goes in `context.page`, which is passed down by reference during
pass 1, so a widget writing to `context.page` writes to the page's own dict, visible to everything
initialized after it.

**The template file is named after the class's module.** `template_path()` takes the file the
widget class is defined in and swaps `.py` for `.html`: a class in `info_card/info_card.py` renders
`info_card/info_card.html`. **A file called `template.html` is never found**; it fails with
`FileNotFoundError` at render time. Override `template_path()` if the template lives elsewhere.
Since files are opened directly rather than resolved through `TEMPLATES` dirs, `{% include %}` of
another component's template is not part of the model: compose with child widgets, or duplicate the
markup.

## Gotchas

**A missing namespace prefix fails silently.** `{{ title }}` is not `{{ data.title }}`; it is simply
undefined, so a `{% if %}` guarding a block is false and the block never renders, with nothing
logged. This is the most common cause of "my widget renders but its content is missing".

**A sync `set_context()` still runs inside the async view.** The whole pipeline runs in the event
loop `as_view()`'s view executes in, and sync or async is only detected per widget with
`inspect.iscoroutinefunction`. A plain `def set_context()` making a synchronous ORM call raises
`SynchronousOnlyOperation`. So does a lazy queryset put in `context.data` and first evaluated by
the template, because every `render_html()` call happens inside the same async pipeline. Fetch with
the async ORM (`aget`, `async for`, and so on) in an `async def set_context()`, and hand templates
evaluated data. A test harness that sets `DJANGO_ALLOW_ASYNC_UNSAFE` hides this.

**`context.children` changes type mid-pipeline.** Code that runs after `_render_children_to_html()`,
such as a `build_response()` override doing work after `await super().build_response()`, sees
`SafeText`, not `Widget`. Inspect the tree before rendering, not after.

**Configuration is read once per process.** `get_config()` caches `settings.WEBSITE_WIDGETS` on
first use, so changing it afterwards, for example with `override_settings` in a test, has no
effect on `show_debug_tree`.
