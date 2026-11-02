# Rendering a widget alone

A widget rendered without a page: into an ordinary Django template, an email or an admin page
from sync code, as an HTML fragment from an async endpoint (an infinite scroller, a "load more"
button), or in a test. Read this before calling `render()` or `arender()`; the lessons
`widgets_in_plain_django.md` and `html_emails.md` show it in use.

Primary code:
- `website_widgets.widget` — `render()`, `arender()`, `render__test()`, `arender__test()`

## The methods

The widget is constructed, adjusted if needed (a value put in `context.page` beforehand reaches
every descendant), then rendered once:

| Method | Runs | For |
|---|---|---|
| `widget.render(request=None)` | a synchronous tree walk, no event loop | sync code: a Django view, an admin hook, an email |
| `await widget.arender(request=None)` | the async pass 1 a page uses | async code: an endpoint returning HTML |
| `widget.render__test(user=None)` / `await widget.arender__test(user=None)` | the same, against a mock `GET /` whose `request.user` is `user` or `AnonymousUser` | tests only |

Each runs the widget's own `set_context()`, then the tree's passes 1 and 3
(`rendering_pipeline.md`), then the widget's template. There is no debug tree and no document
template.

**`render()` never touches an event loop.** It calls each plain `def set_context()` directly, so
the sync ORM works there, and raises `TypeError` naming the widget when it meets an
`async def set_context()`. A widget meant for sync contexts is a `SyncWidget`. `arender()`
awaits async `set_context()`s and calls sync ones, exactly as a page does, so the async ORM trap
in `rendering_pipeline.md` applies to it and not to `render()`.

**Without a request, nothing is mocked.** `self.request` raises, so a widget that needs a request
fails loudly and production code can't end up with a fake one by omission. Templates see
`request` as `None`. Only the `__test` methods build a mock request.

**A widget renders once.** Pass 3 replaces its children with their HTML, so a second render
raises `RuntimeError`; construct a new instance instead. `_render_template()`, which only fills
a template with the context already present, is private: called on a fresh widget it would skip
`set_context()`.

## A fragment or a whole document

A widget renders a fragment, and only a page wraps one in an HTML document, since the document
belongs to the response the page returns. **A whole document that answers no request is a widget
whose template is the document.** An HTML email is one: an `EmailDocument` widget whose template
holds the `<head>`, header and footer every email shares, taking the email's own part as a child
(`EmailDocument(subject='Welcome', content=WelcomeMessage(user=user)).render()`).

**Scripts in an inserted fragment run only if it's inserted the right way.** A widget whose
template starts its controller from a `<script>` keeps doing so in `arender()`'s HTML, but a
`<script>` set through `innerHTML` never runs. The frontend inserts the fragment with
`element.replaceChildren(document.createRange().createContextualFragment(html))` (or
`append()`), whose scripts do run.
