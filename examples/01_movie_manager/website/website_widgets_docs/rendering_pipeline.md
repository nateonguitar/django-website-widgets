# The Rendering Pipeline

What happens between a request arriving at a page and HTML going back out: the order the widget
tree is built and rendered in, and where the async boundary sits. Read this before overriding
`handle_request()` or `build_response()`, or when data doesn't reach a widget. What a template
sees and how its file is found are in `templates.md`; `render()` and `arender()` outside a page
are in `rendering_a_widget_alone.md`.

Primary code:
- `website_widgets.web_page` — `AsyncWebPage` and `SyncWebPage`, each with its `as_view()`,
  `handle_request()` and `build_response()`, and `_WebPage`, the private base they share
- `website_widgets.widget` — `_initialize_widget_tree()` and `_ainitialize_widget_tree()`,
  `_render_children_to_html()`
- `website_widgets.widget_context` — `WidgetContext`
- `website_widgets.config` — `WebsiteWidgetsConfig`, `get_config()`

## Async and sync widgets and pages

A widget subclasses `AsyncWidget` or `SyncWidget`, and a page `AsyncWebPage` or `SyncWebPage`.
Nothing is called plain `Widget` or `WebPage`, so every class says which kind it is, and all four
share a private base, `_Widget`. An `AsyncWidget`'s `set_context()` is `async def`; a
`SyncWidget`'s is plain `def`, or it has none, and it renders everywhere. For pages:

- **`AsyncWebPage`**, the one to use, and what the starter site and `ww_create_page` write. Its
  `set_context()`, `handle_request()` and `build_response()` are `async def`, its view is an
  `async def` view, and it awaits the ORM's async methods (`await Movie.objects.aget(...)`). Its
  widgets may be either kind: an `AsyncWidget`'s `set_context()` is awaited, a `SyncWidget`'s
  called.
- **`SyncWebPage`**, for a page with no async work and a team that would rather write the ORM as
  in any Django view. The same three methods are plain `def`, its view is a plain view, and it
  runs with no event loop. Every widget in it is a `SyncWidget`; an `AsyncWidget` raises
  `TypeError` when the page renders.

Each class checks its subclasses when they're defined (`__init_subclass__`): an `AsyncWidget` or
`AsyncWebPage` with a `def set_context()`, or a `SyncWidget` or `SyncWebPage` with an `async def`
one, raises `TypeError` at import, naming the method and the fix (a page checks
`handle_request()` and `build_response()` too). That check is what lets an override call
`set_context()` directly. Subclassing a private base, `_Widget` or `_WebPage`, raises too.

## One instance per request

`as_view()` is a factory, not Django's class-based view. It returns a view (`async def` for an
`AsyncWebPage`, plain for a `SyncWebPage`) that, for each request, constructs a **fresh page
instance**, assigns `_request` (read as `self.request`), and calls `handle_request()`.

URL parameters are passed to **both** the constructor and `handle_request()`. That is what lets a
page keep them as instance attributes:

```python
class ProfilePage(AsyncWebPage):
    def __init__(self, username: str):
        super().__init__()
        self.username = username
```

Arguments given to `as_view()` itself go to the constructor only, after the URL's positional
arguments.

Because the instance is per-request, instance state is safe. Class-level mutable state is not: it
is shared across every request in the process.

The default `handle_request()` calls the page's own `set_context()`, then `build_response()`. Every
other widget's `set_context()` runs later, inside `build_response()`. An override calls them
directly, `await self.set_context()` on an `AsyncWebPage` and `self.set_context()` on a
`SyncWebPage`.

## `build_response()` runs the tree in four passes

```
1. await self._ainitialize_widget_tree()   every descendant's set_context()
   (self._initialize_widget_tree() on a SyncWebPage)
2. self._generate_debug_tree()             only if show_debug_tree is on
3. self._render_children_to_html()         every descendant's _render_template()
4. self._render_template(), twice         the page's own template, then the document template
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
widget objects and become `SafeText`. After this pass, `context.children` is no longer a tree.

A child value may be a widget, a list of widgets, or `None`:

| Value in `context.children` | Pass 1 | Pass 3 |
|---|---|---|
| a widget | initialized | rendered to `SafeText` |
| `list` of widgets | each initialized | rendered to a list of `SafeText` |
| `list` containing a non-widget | `TypeError` | `TypeError` |
| `None` | skipped | stays `None` |
| anything else | silently skipped | `TypeError` |

A list is iterated in the template with `{% for item in children.items %}`.

Pass 2 sits between 1 and 3 because it needs both: the tree must be fully constructed to be worth
drawing, and the children must still *be* widgets, since the debug tree reports class names and
each widget's optional `debug_label`.

## The constructor or `set_context()`

**The constructor keeps what its arguments already are.** It runs when the widget is built,
before any rendering: `self.request` isn't set yet, `context.page` is still the widget's own
empty dict, and nothing can be awaited. So it stores its arguments, and may put values that need
nothing else in `context.data`, as a repeating widget's `key` does.

**`set_context()` does everything that needs rendering to have started.** It runs once per
render, after `self.request` is set and, for a child, after its parent has handed it the page's
shared `context.page`; every `set_context()` in the tree finishes on the server before any HTML
is sent, so there is no later "on screen" phase. It awaits queries (in an `async def`), reads the
request and the user, writes page-wide values to `context.page`, and builds children from what
it loaded. A widget that needs none of that doesn't override it.

Getting it wrong fails with an explanation rather than silently:

- **Reading `self.request` in a constructor** raises `RuntimeError`, saying it isn't set until
  rendering starts and to read it in `set_context()`.
- **A child writing `context.page` before rendering**, in its constructor or by a parent writing
  `child.context.page[...]`, raises `RuntimeError` when the parent hands it the shared dict,
  naming the keys that would otherwise be lost. A widget rendered on its own keeps a
  `context.page` it was given before `render()`, and a page writes its own whenever it likes,
  since it is the root: only the handover from parent to child checks.
- **A page placed in `context.children`**, directly, in a list, or however it got there, raises
  `TypeError` naming the key: a page is only ever the root, rendered by its view.

## The page's own rendering

**A page renders two templates against the same context.** `self._render_template()` renders the
page's own template. The result has the debug tree appended when one was generated, and is then
passed into the template at `get_document_template_path()` as `page_content_html`. Both renders
see the same `page`, `data` and `children`, so a child widget can be placed in either template:
an appbar in the document template sits outside the page's content but reads the same
`context.page` the page filled.

**The document template is shared; the page's own template is not.** `document_template_path`
names the whole HTML document, `<head>` included, that every page of a kind shares, so it is a
real path, resolved against the concrete class's folder unless absolute. The page's own template
is chosen like any widget's, by module name or `template_filename` (below). An error state that
replaces a page's body is a variant template, not a separate mechanism.

`document_template_path` is `None` on `AsyncWebPage` and `SyncWebPage` themselves, and
`get_document_template_path()` raises `NotImplementedError` until a subclass sets it. The usual
pattern is one intermediate subclass per project that sets the app's document template, kept
beside it, with individual pages inheriting it. Pages that need a different document entirely,
such as an admin area with its own `<head>`, get a second intermediate subclass pointing at a
second document template.

The response is `HttpResponse(html, status=self.status_code)`. `status_code` is a plain class
attribute on both page classes, defaulting to `200`; assign it before `build_response()` to
change it.

## Gotchas

**A widget's sync `set_context()` still runs inside an `AsyncWebPage`'s async view.** That page's
whole pipeline runs in the event loop its view executes in, as does `arender()`'s, and sync or
async is only detected per widget with `inspect.iscoroutinefunction`. A plain `def set_context()`
making a synchronous ORM call there raises `SynchronousOnlyOperation`. So does a lazy queryset put
in `context.data` and first evaluated by the template, because every `_render_template()` call
happens inside the same async pipeline. Fetch with the async ORM (`aget`, `async for`, and so on)
in an `async def set_context()`, and hand templates evaluated data. A test harness that sets
`DJANGO_ALLOW_ASYNC_UNSAFE` hides this. `render()` and a `SyncWebPage` are the exceptions: they run
no event loop, so the sync ORM works in their widgets. `loading_data.md` shows how to write the
widgets so it never comes up.

**What `request.user` holds is up to the project's middleware**, so the template context has no
`user` key:

- **Django's `AuthenticationMiddleware`** sets a lazy object whose first read queries the
  session. Read in an async page, in Python or as `{{ request.user }}`, that raises
  `SynchronousOnlyOperation`, and only for a visitor with a session cookie, which hides it in
  tests. Load it with `await request.auser()` instead.
- **A middleware that sets an already-loaded user** (a sync one, which runs in a worker thread,
  or one that reads the lazy user there) leaves nothing lazy, so reading `request.user` is safe.
  If Django's middleware is installed too, `request.auser()` still reads the session and may
  return a different user.

A page puts the user in `context.page` once, the way its middleware allows, and every widget
reads `page.user`. With Django's middleware:

```python
class AppPage(AsyncWebPage):
    async def handle_request(self, request, *args, **kwargs):
        self.context.page['user'] = await request.auser()
        return await super().handle_request(request, *args, **kwargs)
```

With a middleware that sets a loaded user, `self.context.page['user'] = request.user` instead.

**`context.children` changes type mid-pipeline.** Code that runs after `_render_children_to_html()`,
such as a `build_response()` override doing work after `await super().build_response()`, sees
`SafeText`, not widgets. Inspect the tree before rendering, not after.

**Configuration is read once per process.** `get_config()` caches `settings.WEBSITE_WIDGETS` on
first use, so changing it afterwards, for example with `override_settings` in a test, has no
effect on `show_debug_tree`.
