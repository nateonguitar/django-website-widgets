# The Rendering Pipeline

What happens between a request arriving at a page and HTML going back out: the order the widget
tree is built and rendered in, what a template can see, and where the async boundary sits. The
package's [README](https://github.com/nateonguitar/django-website-widgets#readme) covers the
shapes of the widget and page classes and `WidgetContext`; this covers the order
things run in, which is where the surprises are. Read this before overriding `handle_request()` or
`build_response()`, or when a widget renders but its content is missing.

Primary code:
- `website_widgets.web_page` — `AsyncWebPage` and `SyncWebPage`, each with its `as_view()`,
  `handle_request()` and `build_response()`, and `_WebPage`, the private base they share
- `website_widgets.widget` — `_initialize_widget_tree()` and `_ainitialize_widget_tree()`,
  `_render_children_to_html()`, `get_template_path()`, `_context_dict()`, `_render_template()`,
  `render()` and `arender()`
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

## Rendering a widget outside a page

A widget can be rendered on its own: into an ordinary Django template, an email body or an admin
page from sync code, as an HTML fragment from an async endpoint (an infinite scroller, a "load
more" button), or in a test. The widget is constructed, adjusted if needed (a value put in
`context.page` beforehand reaches every descendant), then rendered once:

| Method | Runs | For |
|---|---|---|
| `widget.render(request=None)` | a synchronous tree walk, no event loop | sync code: a Django view, an admin hook, an email |
| `await widget.arender(request=None)` | the async pass 1 a page uses | async code: an endpoint returning HTML |
| `widget.render__test(user=None)` / `await widget.arender__test(user=None)` | the same, against a mock `GET /` whose `request.user` is `user` or `AnonymousUser` | tests only |

Each runs the widget's own `set_context()`, then passes 1 and 3 above, then the widget's
template. There is no debug tree and no document template.

**`render()` never touches an event loop.** It calls each plain `def set_context()` directly, so
synchronous ORM calls work there, and raises `TypeError` naming the widget when it meets an
`async def set_context()`, which it can't await. A widget meant for sync contexts is written with
`def`. `arender()` awaits async `set_context()`s and calls sync ones, exactly as a page does, so
the async ORM gotcha below applies to it and not to `render()`.

**Without a request, nothing is mocked.** `self.request` raises, so a widget that needs a request
fails loudly and production code can't end up with a fake one by omission. Templates see
`request` as `None`. Only the `__test` methods build a mock request.

This is the line between a widget and a page: a widget renders a fragment, and only a page wraps
one in a whole HTML document, since the document belongs to the response the page returns.

**A whole document that answers no request is a widget whose template is the document.** An HTML
email is one: an `EmailDocument` widget whose template holds the `<head>`, header and footer
every email shares, taking the email's own part as a child widget in its constructor
(`EmailDocument(subject='Welcome', content=WelcomeMessage(user=user)).render()`). Nothing about a
widget's template limits it to a fragment.

**Scripts in an inserted fragment run only if it's inserted the right way.** A widget whose
template starts its controller from a `<script>` keeps doing so in `arender()`'s HTML, but a
`<script>` set through `innerHTML` never runs. The frontend inserts the fragment with
`element.replaceChildren(document.createRange().createContextualFragment(html))` (or
`append()`), whose scripts do run.

**A widget renders once.** Pass 3 replaces its children with their HTML, so a second render
raises `RuntimeError`; construct a new instance instead.

`_render_template()`, which only fills a template with the context already present, is private:
called on a fresh widget it would render an empty template without running `set_context()`.

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

## Templates bypass Django's loader

`_render_template()` opens the template file with `open()`, builds a `Template` from the string, and
renders it against a bare `Context`. Three consequences, all easy to get wrong:

**No template context processors run.** The context is exactly four keys, assembled in
`_context_dict()`:

| Key | Value |
|---|---|
| `request` | the request, or `None` when `render()`/`arender()` was given none |
| `page` | `self.context.page`, shared by reference down the whole tree |
| `data` | `self.context.data`, this widget only |
| `children` | `self.context.children`, this widget only |

Anything a project expects from a context processor (`user`, `csrf_token`, `MEDIA_URL`, `debug`,
settings exposed globally) **is not there** and resolves to empty with no error. `{% load %}`, custom tags
and filters, `{% url %}` and `{% static %}` all work normally; only the automatic context is
absent. The document template additionally receives `page_content_html`, through
`_render_template()`'s `extra_context` argument; application code puts values in
`self.context.data`.

**`data` and `children` are per-widget, `page` is shared.** A child cannot see its parent's `data`.
Anything every widget must reach goes in `context.page`, which is passed down by reference during
pass 1, so a widget writing to `context.page` writes to the page's own dict, visible to everything
initialized after it.

**The template file is named after the class's module** unless `template_filename` says otherwise.
`get_template_path()` takes the file the widget class is defined in and swaps `.py` for `.html`: a
class in `info_card/info_card.py` renders `info_card/info_card.html`. **A file called
`template.html` is never found**; it fails with `FileNotFoundError` at render time.

`template_filename` names another file, and only a bare file name: anything with a `/`, a `\` or
`..` raises `ValueError`. It is read in pass 3 or 4, after every `set_context()` has run, so a
widget can assign it in `set_context()` to choose between templates at runtime: a page with a
not-found state keeps `project_page__not_found.html` beside `project_page.html` and switches to it
there. The package's README suggests that `<module>__<variant>.html` naming.

**The lookup walks the class hierarchy, the concrete class first.** `get_template_path()` checks
the folder of each class in the MRO, skipping the library's own widget and page classes, and returns
the first folder holding the file. A base class's variant, kept beside the base class's module,
therefore works for every subclass, wherever the subclass lives; a subclass with a file of the same
name shadows it. A name found nowhere raises `FileNotFoundError` listing the folders searched.
The module-named default is not searched for: it is always beside the concrete class.

Since files are opened directly rather than resolved through `TEMPLATES` dirs, `{% include %}` of
another component's template is not part of the model: compose with child widgets, or duplicate the
markup.

## Gotchas

**A missing namespace prefix fails silently.** `{{ title }}` is not `{{ data.title }}`; it is simply
undefined, so a `{% if %}` guarding a block is false and the block never renders, with nothing
logged. This is the most common cause of "my widget renders but its content is missing".

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

**What `request.user` holds is up to the project's middleware**, so whether a page can read it
depends on that middleware, not on the package:

- **Django's `AuthenticationMiddleware`**, which `startproject` installs, sets it to a lazy object
  that loads the user from the session on its first read. Read in a page, in Python or as
  `{{ request.user }}`, that first read queries the database inside the async pipeline and
  raises `SynchronousOnlyOperation`, for a visitor with a session cookie only, which hides it in
  tests. Whether the middleware runs sync or async doesn't change this: it stores the lazy object
  either way, and the query runs wherever the object is first read. The middleware also sets
  `request.auser()`, the async way to load the same user.
- **A middleware that sets `request.user` to a user it has already loaded** leaves nothing lazy,
  so reading it in a page is safe. A sync middleware does its database work in the worker thread
  Django adapts it to, where the sync ORM is allowed. So does one that only reads a lazy
  `request.user`, which loads it there. In such a project `request.auser()`, if Django's
  middleware is installed too, still reads the session, so it can return a different user than
  `request.user`.

The package can't know which a project has, so the context has no `user` key. A page that wants
the user puts it in `context.page` once, the way its middleware allows, and every widget reads
`page.user`. With Django's middleware:

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
