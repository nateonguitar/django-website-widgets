# The Rendering Pipeline

What happens between a request arriving at a `Page` and HTML going back out: the order the widget
tree is built and rendered in, what a template can see, and where the async boundary sits. The
package's [README](https://github.com/nateonguitar/django-website-widgets#readme) covers the
shapes of `Widget`, `Page` and `WidgetContext`; this covers the order things run in, which is
where the surprises are. Read this before overriding `handle_request()` or `build_response()`,
or when a widget renders but its content is missing.

Primary code:
- `website_widgets.page` — `Page.as_view()`, `handle_request()`, `build_response()`
- `website_widgets.widget` — `_initialize_widget_tree()` and `_ainitialize_widget_tree()`,
  `_render_children_to_html()`, `get_template_path()`, `_context_dict()`, `_render_template()`,
  `render()` and `arender()`
- `website_widgets.widget_context` — `WidgetContext`
- `website_widgets.config` — `WebsiteWidgetsConfig`, `get_config()`

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
other widget's `set_context()` runs later, inside `build_response()`. An override calls
`await self._acall_set_context()` rather than `set_context()` directly, so a sync or async
`set_context()` both work.

## `build_response()` runs the tree in four passes

```
1. await self._ainitialize_widget_tree()   every descendant's set_context()
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

## Rendering a widget outside a page

A widget can be rendered on its own: into an ordinary Django template, an email body or an admin
page from sync code, as an HTML fragment from an async endpoint (an infinite scroller, a "load
more" button), or in a test. The widget is constructed, adjusted if needed (a value put in
`context.page` beforehand reaches every descendant), then rendered once:

| Method | Runs | For |
|---|---|---|
| `widget.render(request=None)` | a synchronous tree walk, no event loop | sync code: a Django view, an admin hook, an email |
| `await widget.arender(request=None)` | the async pass 1 a page uses | async code: an endpoint returning HTML |
| `widget.render__test(user=None)` / `await widget.arender__test(user=None)` | the same, against a mock `GET /`, `user` or `AnonymousUser` | tests only |

Each runs the widget's own `set_context()`, then passes 1 and 3 above, then the widget's
template. There is no debug tree and no document template.

**`render()` never touches an event loop.** It calls each plain `def set_context()` directly, so
synchronous ORM calls work there, and raises `TypeError` naming the widget when it meets an
`async def set_context()`, which it can't await. A widget meant for sync contexts is written with
`def`. `arender()` awaits async `set_context()`s and calls sync ones, exactly as a page does, so
the async ORM gotcha below applies to it and not to `render()`.

**Without a request, nothing is mocked.** `self.request` raises, so a widget that needs a request
fails loudly and production code can't end up with a fake one by omission. Templates see
`request` and `user` as `None`. Only the `__test` methods build a mock request.

This is the line between a widget and a page: a widget renders a fragment, and only a page wraps
one in a whole HTML document, since the document belongs to the response the page returns.

**A whole document that answers no request is a widget whose template is the document.** An HTML
email is one: an `EmailDocument` widget whose template holds the `<head>`, header and footer
every email shares, taking the email's own part as a child widget in its constructor
(`EmailDocument(subject='Welcome', content=WelcomeMessage(user=user)).render()`). Nothing about a
widget's template limits it to a fragment.

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

`document_template_path` is `None` on `Page` itself, and `get_document_template_path()` raises
`NotImplementedError` until a subclass sets it. The usual pattern is one intermediate subclass per
project that sets the app's document template, kept beside it, with individual pages inheriting
it. Pages that need a different document entirely, such as an admin area with its own `<head>`,
get a second intermediate subclass pointing at a second document template.

The response is `HttpResponse(html, status=self.status_code)`. `status_code` is a plain class
attribute on `Page`, defaulting to `200`; assign it before `build_response()` to change it.

## Templates bypass Django's loader

`_render_template()` opens the template file with `open()`, builds a `Template` from the string, and
renders it against a bare `Context`. Three consequences, all easy to get wrong:

**No template context processors run.** The context is exactly five keys, assembled in
`_context_dict()`:

| Key | Value |
|---|---|
| `request` | the request, or `None` when `render()`/`arender()` was given none |
| `user` | `request.user`, or `None` without a request or without `django.contrib.auth` |
| `page` | `self.context.page`, shared by reference down the whole tree |
| `data` | `self.context.data`, this widget only |
| `children` | `self.context.children`, this widget only |

Anything a project expects from a context processor (`csrf_token`, `MEDIA_URL`, `debug`, settings
exposed globally) **is not there** and resolves to empty with no error. `{% load %}`, custom tags
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
the folder of each class in the MRO, skipping the library's own `Widget` and `Page`, and returns
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

**A sync `set_context()` still runs inside the async view.** A page's whole pipeline runs in the
event loop `as_view()`'s view executes in, as does `arender()`'s, and sync or async is only
detected per widget with `inspect.iscoroutinefunction`. A plain `def set_context()` making a
synchronous ORM call there raises `SynchronousOnlyOperation`. So does a lazy queryset put in
`context.data` and first evaluated by the template, because every `_render_template()` call
happens inside the same async pipeline. Fetch with the async ORM (`aget`, `async for`, and so on)
in an `async def set_context()`, and hand templates evaluated data. A test harness that sets
`DJANGO_ALLOW_ASYNC_UNSAFE` hides this. `render()` is the exception: called from sync code, it
runs no event loop, so the sync ORM works in its widgets.

**`context.children` changes type mid-pipeline.** Code that runs after `_render_children_to_html()`,
such as a `build_response()` override doing work after `await super().build_response()`, sees
`SafeText`, not `Widget`. Inspect the tree before rendering, not after.

**Configuration is read once per process.** `get_config()` caches `settings.WEBSITE_WIDGETS` on
first use, so changing it afterwards, for example with `override_settings` in a test, has no
effect on `show_debug_tree`.
