# The Rendering Pipeline

What happens between a request arriving at a `Page` and HTML going back out. The README
covers the shapes of `Widget`, `Page` and `Context`; this covers the order things run in,
which is where the surprises are.

Primary code: `website_widgets/page.py`, `website_widgets/widget.py`

## One instance per request

`Page.as_view()` is a factory, not Django's class-based view. For each request it constructs
a **fresh page instance**, assigns `_request` (read as `self.request`), and calls
`handle_request()`, awaiting it if it is a coroutine.

URL parameters are passed to **both** the constructor and `handle_request()`. That is what
lets a page keep them as instance attributes:

```python
class ProfilePage(Page):
    def __init__(self, username: str):
        super().__init__()
        self.username = username
```

Because the instance is per-request, instance state is safe. Class-level mutable state is
not — it is shared across every request in the process.

## `build_response()` runs the tree in four passes

```
1. await self._initialize_widget_tree()    every descendant's set_context()
2. self._generate_debug_tree()             if show_debug_tree is on
3. await self._render_children_to_html()   every descendant's render_html()
4. self.html()  → render base template     the page's own template, then the wrapper
```

**Pass 1 is depth-first and parent-before-child.** For each child widget the tree walker
assigns `_request`, **shares `context.page` by reference**, calls `set_context()` (awaiting it
only if it is a coroutine function), and then recurses into that widget's own children. So a
widget's `set_context()` may freely construct more children; they are initialized on the way
down.

The ordering consequence that catches people: **a parent's `set_context()` has already
returned before any child's runs.** A parent cannot read a child's `context.data`. Data flows
down through constructor arguments, never up.

**Pass 3 replaces the widgets with their HTML.** `_render_children_to_html()` renders children
before their parent and then overwrites `self.context.children` — the dict's values stop being
`Widget` objects and become `SafeText`. After this pass, `context.children` is no longer a tree.

A child value may be a `Widget`, a `list[Widget]`, or `None`. A list renders to a list of
`SafeText`, iterated in the template with `{% for item in children.items %}`. Anything else
raises `TypeError` in both passes.

Pass 2 sits between 1 and 3 deliberately: the tree must be fully constructed to be worth
drawing, but the widgets must still *be* widgets, since the debug tree reports class names.

## The page's own rendering

`self.html()` returns `self.render_html()`, which renders the page's `template.html`. The
result — or `self._override_main_content_html` if that attribute is set — is then passed into
the template at `base_template_path()` as `main_content_html`.

`base_template_path()` raises `NotImplementedError` on `Page` itself. The usual pattern is one
intermediate subclass per project that returns the app's base template, with individual pages
inheriting it.

`_override_main_content_html` is the escape hatch for replacing a page's body while keeping
the wrapper — an error state, say. Set it before calling `build_response()` and the page's own
template is not rendered at all.

The response is `HttpResponse(html, status=self.status_code)`. `status_code` is a plain class
attribute on `Page`, defaulting to `200`; assign it before `build_response()` to change it.

## Templates bypass Django's loader entirely

`render_html()` opens the template file with `open()`, builds a `Template` from the string, and
renders it against a bare `Context`. Two consequences, both easy to get wrong:

**No template context processors run.** The context is exactly five keys, assembled in
`_context_dict()`:

| Key | Value |
|---|---|
| `request` | `self.request` |
| `user` | `self.request.user` |
| `page` | `self.context.page`, shared by reference down the whole tree |
| `data` | `self.context.data`, this widget only |
| `children` | `self.context.children`, this widget only |

Anything a project expects from a context processor — `csrf_token`, `MEDIA_URL`, `debug`,
settings exposed globally — **is not there** and resolves to empty with no error. `{% load %}`,
custom tags and filters, `{% url %}` and `{% static %}` all work normally; it is only the
automatic context that is absent.

**`data` and `children` are per-widget, `page` is shared.** A child cannot see its parent's
`data`. Anything every widget must reach goes in `context.page`, which is passed down by
reference during pass 1 — meaning a widget writing to `context.page` writes to the page's own
dict, visible to everything initialized after it.

**Template paths are resolved from the class's own file.** `template_path()` defaults to
`template.html` beside the widget class; override it if the template lives elsewhere. Since
files are opened directly rather than resolved through `TEMPLATES` dirs, `{% include %}` of
another component's template is not part of the model — compose with child widgets, or
duplicate the markup.

`render_html()`'s `extra_context` argument exists for the library's own use, passing
`main_content_html` into the base template. Application code should put values in
`self.context.data`.

## Gotchas

**A missing namespace prefix fails silently.** `{{ title }}` is not `{{ data.title }}`; it is
simply undefined, so a `{% if %}` guarding a block is false and the block never renders, with
nothing logged. This is the most common cause of "my widget renders but its content is
missing".

**`set_context()` may be sync or async, and the distinction is detected per widget** with
`inspect.iscoroutinefunction`. Declare it `async` only when something inside is awaited; a
non-async `set_context()` containing an un-awaited coroutine fails at render time, not at
definition.

**`context.children` changes type mid-pipeline.** Code that runs after
`_render_children_to_html()` — anything overriding `build_response()` and doing work after
`await super().build_response()` — sees `SafeText`, not `Widget`. Inspect the tree before
rendering, not after.
